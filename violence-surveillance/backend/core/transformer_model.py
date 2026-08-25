"""Architecture ViolenceTransformer (identique au pipeline d'entraînement)."""

import math
import torch
import torch.nn as nn


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=512, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
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
        self.attn = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        self.drop1 = nn.Dropout(dropout)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
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
    def __init__(
        self,
        feature_dim=20,
        d_model=256,
        n_heads=8,
        n_layers=4,
        d_ff=512,
        dropout=0.35,
        max_seq_len=512,
    ):
        super().__init__()
        self.d_model = d_model

        self.input_proj = nn.Sequential(
            nn.Linear(feature_dim, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
        )

        b = d_model // 3
        self.conv_short = nn.Sequential(
            nn.Conv1d(d_model, b, 3, padding=1),
            nn.BatchNorm1d(b), nn.GELU(), nn.Dropout(dropout * 0.3),
        )
        self.conv_mid = nn.Sequential(
            nn.Conv1d(d_model, b, 7, padding=3),
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

        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
        self.pos_enc = SinusoidalPositionalEncoding(d_model, max_seq_len, dropout)

        self.layers = nn.ModuleList([
            TransformerEncoderBlock(d_model, n_heads, d_ff, dropout)
            for _ in range(n_layers)
        ])

        drop_probs = [i * 0.1 / n_layers for i in range(n_layers)]
        self.drop_paths = nn.ModuleList([nn.Dropout(p) for p in drop_probs])
        self.final_norm = nn.LayerNorm(d_model)

        pool_dim = d_model * 3
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
        x = self.input_proj(x)

        xt = x.transpose(1, 2)
        conv_out = torch.cat([
            self.conv_short(xt),
            self.conv_mid(xt),
            self.conv_long(xt),
        ], dim=1).transpose(1, 2)
        x = x + self.conv_merge(conv_out)

        cls = self.cls_token.expand(x.size(0), -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = self.pos_enc(x)

        if padding_mask is not None:
            cls_mask = torch.zeros(x.size(0), 1, dtype=torch.bool, device=x.device)
            padding_mask = torch.cat([cls_mask, padding_mask], dim=1)

        attns = []
        for layer, drop_path in zip(self.layers, self.drop_paths):
            x_new, attn_w = layer(x, mask=padding_mask)
            if self.training:
                x = x + drop_path(x_new - x)
            else:
                x = x_new
            attns.append(attn_w)

        x = self.final_norm(x)
        cls_out = x[:, 0]
        seq_out = x[:, 1:]
        mean_pool = seq_out.mean(dim=1)
        max_pool = seq_out.max(dim=1).values
        pooled = torch.cat([cls_out, mean_pool, max_pool], dim=1)

        logits = torch.sigmoid(self.classifier(pooled))
        return logits, attns
