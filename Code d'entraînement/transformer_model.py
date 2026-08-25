# transformer_model.py — Version anti-overfitting

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import config


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=512, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe  = torch.zeros(max_len, d_model)
        pos = torch.arange(max_len, dtype=torch.float).unsqueeze(1)
        div = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float)
            * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x):
        return self.dropout(x + self.pe[:, :x.size(1)])


class TransformerEncoderBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn  = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        self.drop1 = nn.Dropout(dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff    = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),   # dropout supplémentaire dans FFN
        )
        self.drop2 = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        residual = x
        attn_out, attn_w = self.attn(
            self.norm1(x), self.norm1(x), self.norm1(x),
            key_padding_mask=mask, need_weights=True,
            average_attn_weights=True,
        )
        x = residual + self.drop1(attn_out)
        residual = x
        x = residual + self.drop2(self.ff(self.norm2(x)))
        return x, attn_w


class ViolenceTransformer(nn.Module):
    """
    Architecture anti-overfitting :
        - Dropout 0.4 partout
        - StochasticDepth (DropPath)
        - Weight decay fort (via optimizer)
        - N_LAYERS réduit à 4
        - Features 20D
        - MixedPooling (CLS + Mean + Max)
    """

    def __init__(
        self,
        feature_dim = config.FEATURE_DIM,   # 20
        d_model     = config.D_MODEL,        # 256
        n_heads     = config.N_HEADS,        # 8
        n_layers    = config.N_LAYERS,       # 4
        d_ff        = config.D_FF,           # 512
        dropout     = config.DROPOUT,        # 0.4
        max_seq_len = config.MAX_SEQ_LEN,
    ):
        super().__init__()
        self.d_model = d_model

        # ── Input projection ──────────────────────────────────────────────
        self.input_proj = nn.Sequential(
            nn.Linear(feature_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
        )

        # ── Conv temporel multi-échelle (3 branches) ──────────────────────
        b = d_model // 3
        self.conv_short = nn.Sequential(
            nn.Conv1d(d_model, b, 3,  padding=1),
            nn.BatchNorm1d(b), nn.GELU(), nn.Dropout(dropout * 0.3),
        )
        self.conv_mid = nn.Sequential(
            nn.Conv1d(d_model, b, 7,  padding=3),
            nn.BatchNorm1d(b), nn.GELU(), nn.Dropout(dropout * 0.3),
        )
        self.conv_long = nn.Sequential(
            nn.Conv1d(d_model, b, 15, padding=7),
            nn.BatchNorm1d(b), nn.GELU(), nn.Dropout(dropout * 0.3),
        )
        self.conv_merge = nn.Sequential(
            nn.Linear(b * 3, d_model),
            nn.LayerNorm(d_model),
            nn.Dropout(dropout * 0.4),
        )

        # ── CLS token ─────────────────────────────────────────────────────
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)

        # ── Positional encoding ───────────────────────────────────────────
        self.pos_enc = SinusoidalPositionalEncoding(d_model, max_seq_len, dropout)

        # ── Transformer (4 layers) ────────────────────────────────────────
        self.layers = nn.ModuleList([
            TransformerEncoderBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        # ── StochasticDepth (DropPath) ────────────────────────────────────
        # Probabilité de drop croissante par layer
        drop_probs = [i * 0.1 / n_layers for i in range(n_layers)]
        self.drop_paths = nn.ModuleList([
            nn.Dropout(p) for p in drop_probs
        ])

        self.final_norm = nn.LayerNorm(d_model)

        # ── Multi-scale pooling → 3×d_model ──────────────────────────────
        pool_dim = d_model * 3

        # ── Classifier avec forte régularisation ─────────────────────────
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(pool_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.LayerNorm(d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(d_model // 2, 1),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x, padding_mask=None):
        B, T, _ = x.shape

        # Input projection
        x = self.input_proj(x)

        # Conv temporel
        xt = x.transpose(1, 2)
        conv_out = torch.cat([
            self.conv_short(xt),
            self.conv_mid(xt),
            self.conv_long(xt),
        ], dim=1).transpose(1, 2)
        x = x + self.conv_merge(conv_out)

        # CLS + positional encoding
        cls = self.cls_token.expand(B, -1, -1)
        x   = torch.cat([cls, x], dim=1)
        x   = self.pos_enc(x)

        # Mask CLS
        if padding_mask is not None:
            cls_mask     = torch.zeros(B, 1, dtype=torch.bool, device=x.device)
            padding_mask = torch.cat([cls_mask, padding_mask], dim=1)

        # Transformer avec stochastic depth
        attns = []
        for layer, drop_path in zip(self.layers, self.drop_paths):
            x_new, attn_w = layer(x, mask=padding_mask)
            # Stochastic depth : skip connection aléatoire
            if self.training:
                x = x + drop_path(x_new - x)
            else:
                x = x_new
            attns.append(attn_w)

        x = self.final_norm(x)

        # Multi-scale pooling
        cls_out   = x[:, 0]
        seq_out   = x[:, 1:]
        mean_pool = seq_out.mean(dim=1)
        max_pool  = seq_out.max(dim=1).values
        pooled    = torch.cat([cls_out, mean_pool, max_pool], dim=1)

        logits = torch.sigmoid(self.classifier(pooled))
        return logits, attns


def build_model(device=None):
    device = device or config.DEVICE
    model  = ViolenceTransformer().to(device)
    n_p    = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"✓ ViolenceTransformer | params={n_p:,} | "
          f"feat={config.FEATURE_DIM}D | "
          f"d={config.D_MODEL} | L={config.N_LAYERS} | "
          f"dropout={config.DROPOUT}")
    return model