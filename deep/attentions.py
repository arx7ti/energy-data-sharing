#!/usr/bin/env python


# from matplotlib import pyplot
# from scipy.signal import resample
from torch.nn.functional import relu
from numpy import concatenate, greater, diff, where
from torch.nn import (
    Module,
    DataParallel,
    Transformer,
    Upsample,
    Conv2d,
    Sequential,
    ConvTranspose2d,
    BatchNorm2d,
    LayerNorm,
    ReLU,
    MaxPool2d,
    Linear,
    AvgPool2d,
    Dropout,
    LSTM,
    init,
    Sigmoid,
    Softmax,
)
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

# from torch.fft import rfft, fft
from torch.nn.functional import (
    l1_loss,
    cross_entropy,
    binary_cross_entropy,
    softmax,
    dropout,
)
from torch import (
    tensor,
    zeros_like,
    bmm,
    cat,
    stack,
    randn,
    arange,
    sin,
    float32,
    unsqueeze,
    zeros,
    ones,
    flatten,
    reshape,
    exp,
    nonzero,
    from_numpy,
    randperm,
    log,
    flip,
    sin,
    stft,
    sqrt,
    atan2,
    log10,
    linspace,
    hann_window,
    sigmoid,
    cdist,
    full,
    int64,
    clamp,
    max as tensor_max,
    min as tensor_min,
    abs as tensor_abs,
)


t1 = arange(0, 1000, dtype=float32)
x1 = zeros(1000)
x2 = 100 * sin(2 * 3.14 * 50 * t1.to(dtype=float32))
x3 = 50 * (
    sin(2 * 3.14 * 150 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 50 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 250 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 350 * t1.to(dtype=float32))
)
x4 = zeros(1000)
x5 = 100 * sin(2 * 3.14 * 500 * t1.to(dtype=float32))
y1 = ones(1000)
y0 = zeros(1000)
x = cat([x1, x2, x3, x1, x5])
# y_1 = cat([y1, y0, y0, y1, y1])
# y_2 = cat([y0, y1, y0, y0, y1])
# y_3 = cat([y0, y0, y1, y0, y1])
# y_4 = cat([y0, y0, y1, y0, y1])
# y_5 = cat([y0, y0, y1, y0, y1])
y = cat([y0, y1, y1, y0, y1])
x = stack(5 * [x])
y = stack(5 * [y])


class ResidualBlock(Module):
    def __init__(self, input_channels, output_channels, receptive_field, stride=1):
        super().__init__()
        if isinstance(receptive_field, int):
            padding = receptive_field // 2
        elif isinstance(receptive_field, tuple):
            padding = tuple(map(lambda x: x // 2, receptive_field))
        self.conv_1 = Sequential(
            Conv2d(
                input_channels,
                output_channels,
                receptive_field,
                padding=padding,
                stride=stride,
            ),
            # BatchNorm2d(output_channels, track_running_stats=False),
            ReLU(True),
        )
        self.conv_2 = Sequential(
            Conv2d(output_channels, output_channels, receptive_field, padding=padding),
            # BatchNorm2d(output_channels, track_running_stats=False),
        )
        self.conv_3 = Sequential(
            Conv2d(input_channels, output_channels, kernel_size=1, stride=stride),
            # Dropout(0.1),
        )
        self.dropout = Dropout(0.1)

    def forward(self, x):
        y = self.conv_2(self.conv_1(x))
        if x.size() != y.size():
            x = self.conv_3(x)
        y = self.dropout(y)
        y = y + x
        return relu(y)


class ResNextBlock(Module):
    def __init__(
        self,
        input_channels,
        output_channels,
        receptive_field,
        groups,
        stride=1,
        expansion=1,
    ):
        super().__init__()
        if isinstance(receptive_field, int):
            padding = receptive_field // 2
        elif isinstance(receptive_field, tuple):
            padding = tuple(map(lambda x: x // 2, receptive_field))
        groups_width = output_channels * groups
        self.unity_convolution_1 = Conv2d(input_channels, groups_width, 1)
        self.grouped_convolution = Sequential(
            Conv2d(
                groups_width,
                groups_width,
                receptive_field,
                padding=padding,
                stride=stride,
                groups=groups,
            ),
            ReLU(True),
        )
        self.unity_convolution_2 = Conv2d(groups_width, expansion * groups_width, 1)
        self.residual = Conv2d(
            input_channels, expansion * groups_width, 1, stride=stride
        )
        self.dropout = Dropout(0.1)

    def forward(self, x):
        y = self.unity_convolution_2(
            self.grouped_convolution(self.unity_convolution_1(x))
        )
        if x.size() != y.size():
            x = self.residual(x)
        y = self.dropout(y)
        y = y + x
        return relu(y)


class DotProductAttention(Module):
    def __init__(self):
        super().__init__()

    def forward(self, q, k, v):
        scale_factor = k.size(-1)
        scores = 1 / scale_factor ** 0.5 * (q @ k.transpose(2, 3))
        weights = softmax(scores, dim=-1)
        output = weights @ v
        return output


class MultiHeadAttention(Module):
    def __init__(self, d, h, dq, dv):
        super().__init__()
        self.d = d
        self.h = h
        self.dq = dq
        self.dv = dv
        self.query_weights = Linear(d, h * dq, bias=False)
        self.key_weights = Linear(d, h * dq, bias=False)
        self.values_weights = Linear(d, h * dv, bias=False)
        self.attention = DotProductAttention()
        self.ffn = Linear(h * dv, d, bias=False)
        self.norm = LayerNorm(d, eps=1e-6)
        self.dropout = Dropout(0.1)

    def forward(self, q, k, v):
        residual = q
        bs, len_q, len_k, len_v = q.size(0), q.size(1), k.size(1), v.size(1)
        q = self.query_weights(q).view(bs, len_q, self.h, self.dq).transpose(1, 2)
        k = self.key_weights(k).view(bs, len_k, self.h, self.dv).transpose(1, 2)
        v = self.values_weights(v).view(bs, len_v, self.h, self.dv).transpose(1, 2)
        attention = self.attention(q, k, v)
        attention = attention.transpose(1, 2).reshape(bs, len_q, -1)
        attention = self.ffn(attention)
        attention = self.dropout(attention)
        attention = self.norm(attention + residual)
        # print("attention:", attention.shape)
        return attention


class Model(Module):
    def __init__(self, nloads):
        super(Model, self).__init__()
        self.norm0 = BatchNorm2d(1)
        self.norm0.bias.data.fill_(0.0)
        self.norm0.weight.data.fill_(1.0)
        self.encoder = Sequential(
            ResidualBlock(1, 32, 3),
            ResidualBlock(32, 32, 3),
            AvgPool2d((4, 2)),
            ResidualBlock(32, 64, 3),
            ResidualBlock(64, 64, 3),
            # ResidualBlock(64, 64, 3),
            # ResidualBlock(64, 64, 3),
            AvgPool2d((4, 2)),
            ResidualBlock(64, 128, 3),
            ResidualBlock(128, 128, 3),
            # ResidualBlock(128, 128, 3),
            # ResidualBlock(128, 128, 3),
            # ResidualBlock(128, 128, 3),
            # ConvTranspose2d(256, 256, (1, 8), (1, 8)),
            # ResidualBlock(256, 256, 3),
        )
        self.avg_pool = AvgPool2d((4, 2))
        self.max_pool = MaxPool2d((4, 2))
        self.embedding = Sequential(ConvTranspose2d(128, 128, (1, 4), (1, 4)))
        # self.encoder = Sequential(
        #     ResNextBlock(1, 4, 5, groups=4),
        #     # ResNextBlock(16, 16, 5, groups=4),
        #     AvgPool2d((4, 2)),
        #     ResNextBlock(32, 8, 3, groups=4),
        #     # ResNextBlock(32, 32, 3, groups=4),
        #     AvgPool2d((4, 2)),
        #     ResNextBlock(64, 16, 3, groups=4),
        #     # ResNextBlock(64, 64, 3, groups=4),
        #     AvgPool2d((4, 2)),
        #     ResNextBlock(128, 32, 3, groups=4),
        #     # ResNextBlock(128, 128, 3, groups=4),
        # )
        self.attention1 = MultiHeadAttention(128, 2, 64, 64)
        self.ffn1 = Sequential(Linear(128, 64), ReLU(True), Linear(64, 128))
        # self.attention2 = MultiHeadAttention(256, 4, 64, 64)
        # self.ffn2 = Sequential(Linear(256, 64), ReLU(True), Linear(64, 256))
        # self.transformer = Transformer(
        #     d_model=128,
        #     nhead=2,
        #     num_encoder_layers=3,
        #     num_decoder_layers=3,
        #     dim_feedforward=512,
        # )
        self.labels = Sequential(
            Linear(128, 128), ReLU(True), Linear(128, nloads), Sigmoid(),
        )
        self.norm1 = LayerNorm(128, eps=1e-6)
        self.dropout1 = Dropout(0.1)
        # self.norm2 = LayerNorm(256, eps=1e-6)
        # self.dropout2 = Dropout(0.1)

    def forward(self, x, t=None):
        # win_len = 63
        win_len = 127
        hop_size = 25
        # hop_size = 50
        x = stft(
            x,
            n_fft=win_len,
            hop_length=hop_size,
            window=hann_window(win_len).to(device=x.device),
            # return_complex=True,
            normalized=True,
        )
        x = sqrt(x[..., 0].pow(2) + x[..., 1].pow(2))
        # print("stft:", x.shape)
        # x = tensor_abs(x)
        x = unsqueeze(x, 1)
        x = self.norm0(x)
        y = self.encoder(x)
        y_m = self.max_pool(y)
        y_a = self.avg_pool(y)
        y = self.embedding(y_m + y_a)
        # y = y_m + y_a
        # print("backbone:", y.shape)
        bs, chls, freqs, frames = y.size()
        # s = y.permute(-1, 0, 1, 2)
        # s = s.contiguous().reshape(frames, bs, freqs * chls)
        s = y.permute(0, 3, 1, 2)
        s = s.contiguous().reshape(bs, frames, freqs * chls)
        # print("sequence:", s.shape)
        a = self.attention1(s, s, s)
        r = a
        a = self.dropout1(self.ffn1(a))
        a = self.norm1(a + r)
        # a = self.attention2(a, a, a)
        # r = a
        # a = self.dropout2(self.ffn2(a))
        # a = self.norm2(a + r)
        # a = self.transformer(s, zeros_like(s)).permute(1, 0, -1)
        # print(a.shape)
        l = self.labels(a)
        # t = t[:, :: (0 + t.size(1) // l.size(1))]
        return l


# m = Model(3)
# m(x, y)
