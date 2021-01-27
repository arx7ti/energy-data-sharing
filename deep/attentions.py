#!/usr/bin/env python


# from matplotlib import pyplot
from scipy.signal import resample, resample_poly
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
from torch.fft import rfft, fft
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
    sqrt,
    atan2,
    log10,
    linspace,
    sigmoid,
    cdist,
    full,
    int64,
    clamp,
    stft,
    hann_window,
    log,
    abs as tensor_abs,
    max as tensor_max,
    min as tensor_min,
)


t1 = arange(0, 1000, dtype=float32)
x1 = zeros(1000)
x2 = 100 * sin(2 * 3.14 * 50 * t1.to(dtype=float32))
x3 = 50 * (
    sin(2 * 3.14 * 150 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 50 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 250 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 350 * t1.to(dtype=float32))
    + sin(2 * 3.14 * 850 * t1.to(dtype=float32))
)
x4 = zeros(1000)
x5 = 100 * sin(2 * 3.14 * 500 * t1.to(dtype=float32))
y1 = ones(1000)
y0 = zeros(1000)
x = cat([x1, x2, x3, x1, x5])
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
            Dropout(0.1),
            # BatchNorm2d(output_channels),
            ReLU(True),
        )
        self.conv_2 = Sequential(
            Conv2d(output_channels, output_channels, receptive_field, padding=padding),
            Dropout(0.1),
            # BatchNorm2d(output_channels),
        )
        self.conv_3 = Sequential(
            Conv2d(input_channels, output_channels, kernel_size=1, stride=stride),
            Dropout(0.1),
        )
        # self.dropout = Dropout(0.1)

    def forward(self, x):
        y = self.conv_2(self.conv_1(x))
        if x.size() != y.size():
            x = self.conv_3(x)
        # y = self.dropout(y)
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
        return attention


class Model(Module):
    def __init__(self, nloads):
        super(Model, self).__init__()
        self.norm0 = BatchNorm2d(1)
        # self.norm0.bias.data.fill_(0.0)
        # self.norm0.weight.data.fill_(1.0)
        self.encoder = Sequential(
            ResidualBlock(1, 32, 3),
            AvgPool2d((16, 1)),
            ResidualBlock(32, 64, 3),
            AvgPool2d((4, 1)),
            ResidualBlock(64, 128, 3),
            MaxPool2d((4, 1)),
            ResidualBlock(128, 256, 3),
            # ResidualBlock(256, 256, 3),
            MaxPool2d((4, 1)),
            ResidualBlock(256, 512, 3),
            # ResidualBlock(512, 512, 3),
            # ResidualBlock(512, 512, 3),
        )
        self.avg_pool = AvgPool2d((2, 1))
        self.max_pool = MaxPool2d((2, 1))
        # self.embedding = ConvTranspose2d(128, 128, (1, 50), stride=(1, 2))
        self.attention1 = MultiHeadAttention(512, 8, 64, 64)
        self.ffn1 = Sequential(Linear(512, 64), ReLU(True), Linear(64, 512))
        self.labels = Sequential(
            Linear(512, 256), Dropout(0.1), ReLU(True), Linear(256, nloads), Sigmoid(),
        )
        self.norm1 = LayerNorm(512, eps=1e-6)
        self.dropout1 = Dropout(0.1)

    def forward(self, x):
        # x = self.spectrogram(x)
        window_length = 1024
        # hop_size = window_length // 2
        hop_size = window_length
        x = rfft(x, dim=-1, norm="forward")
        # x = stft(
        #     x,
        #     n_fft=window_length,
        #     hop_length=hop_size,
        #     window=hann_window(window_length).to(device=x.device),
        #     return_complex=True,
        #     normalized=True,
        # )
        # print("stft:", x.shape)
        x = tensor_abs(x)
        x = 2 * log(x + 1e-9)
        x = unsqueeze(x, 1)
        x = unsqueeze(x, -1)
        x = self.norm0(x)
        y = self.encoder(x)
        # print("backbone:", y.shape)
        y_m = self.max_pool(y)
        y_a = self.avg_pool(y)
        # y = self.embedding(y_m + y_a)
        y = y_m + y_a
        # y = y_m
        # print("backbone:", y.shape)
        bs, chls, freqs, frames = y.size()
        s = y.permute(0, 3, 1, 2)
        s = s.contiguous().reshape(bs, frames, freqs * chls)
        # print("sequence:", s.shape)
        a = self.attention1(s, s, s)
        r = a
        a = self.dropout1(self.ffn1(a))
        a = self.norm1(a + r)
        # print(a.shape)
        l = self.labels(a)
        return l
        # return x


# print(x.shape)
# m = Model(3)
# x = m(x)
# pyplot.plot(where(resample(y[0], 6) > 0.6, 1, 0))
# print(y[0][::1000])
# pyplot.imshow(x[0])
# pyplot.show()
