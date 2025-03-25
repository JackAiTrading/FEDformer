import argparse
import os
import sys
import torch
from exp.exp_main import Exp_Main
import random
import numpy as np


def main():
    fix_seed = 2021
    random.seed(fix_seed)
    torch.manual_seed(fix_seed)
    np.random.seed(fix_seed)

    parser = argparse.ArgumentParser(description='Autoformer & Transformer family for Time Series Forecasting')

    # 基础配置
    parser.add_argument('--is_training', type=int, default=1, help='训练模式开关 1开启/0关闭')
    parser.add_argument('--task_id', type=str, default='test', help='任务标识ID')
    parser.add_argument('--model', type=str, default='FEDformer',
                        help='模型名称，可选: [FEDformer, Autoformer, Informer, Transformer]')

    # FEDformer模型补充配置
    parser.add_argument('--version', type=str, default='Fourier',
                        help='FEDformer版本选择，可选: [Fourier傅里叶, Wavelets小波]')
    parser.add_argument('--mode_select', type=str, default='random',
                        help='模式选择方法，可选: [random随机, low低频]')
    parser.add_argument('--modes', type=int, default=64, help='随机选择的模式数量')
    parser.add_argument('--L', type=int, default=3, help='忽略层级数')
    parser.add_argument('--base', type=str, default='legendre', help='MWT基函数类型')
    parser.add_argument('--cross_activation', type=str, default='tanh',
                        help='交叉注意力激活函数，可选: [tanh, softmax]')

    # 数据加载配置
    parser.add_argument('--data', type=str, default='ETTh1', help='数据集类型')
    parser.add_argument('--root_path', type=str, default='./resource/dataset/ETT-small/', help='数据文件根目录路径')
    parser.add_argument('--data_path', type=str, default='ETTh1.csv', help='数据文件名')
    parser.add_argument('--features', type=str, default='M',
                        help='预测任务类型，可选:[M, S, MS]; M:多变量预测多变量, '
                             'S:单变量预测单变量, MS:多变量预测单变量')
    parser.add_argument('--target', type=str, default='OT', help='S或MS任务中的目标特征')
    parser.add_argument('--freq', type=str, default='h',
                        help='时间特征编码频率，可选:[s:秒级, t:分钟级, h:小时级, d:天级, '
                             'b:工作日, w:周级, m:月级], 也可使用更细粒度如15min或3h')
    parser.add_argument('--detail_freq', type=str, default='h', help='预测时使用的时间频率，格式同freq')
    parser.add_argument('--checkpoints', type=str, default='./checkpoints/', help='模型检查点保存路径')

    # 预测任务配置
    parser.add_argument('--seq_len', type=int, default=96, help='输入序列长度')
    parser.add_argument('--label_len', type=int, default=48, help='起始标记长度')
    parser.add_argument('--pred_len', type=int, default=96, help='预测序列长度')
    # parser.add_argument('--cross_activation', type=str, default='tanh'

    # 模型定义
    parser.add_argument('--enc_in', type=int, default=7, help='编码器输入维度')
    parser.add_argument('--dec_in', type=int, default=7, help='解码器输入维度')
    parser.add_argument('--c_out', type=int, default=7, help='输出维度')
    parser.add_argument('--d_model', type=int, default=512, help='模型隐层维度')
    parser.add_argument('--n_heads', type=int, default=8, help='注意力头数量')
    parser.add_argument('--e_layers', type=int, default=2, help='编码器层数')
    parser.add_argument('--d_layers', type=int, default=1, help='解码器层数')
    parser.add_argument('--d_ff', type=int, default=2048, help='前馈网络维度')
    parser.add_argument('--moving_avg', default=[24], help='滑动平均窗口大小')
    parser.add_argument('--factor', type=int, default=1, help='注意力因子')
    parser.add_argument('--distil', action='store_false',
                        help='是否在编码器使用蒸馏技术，添加此参数表示禁用',
                        default=True)
    parser.add_argument('--dropout', type=float, default=0.05, help='丢弃率')
    parser.add_argument('--embed', type=str, default='timeF',
                        help='时间特征编码方式，可选:[timeF, fixed固定, learned学习]')
    parser.add_argument('--activation', type=str, default='gelu', help='激活函数类型')
    parser.add_argument('--output_attention', action='store_true', help='是否输出编码器注意力权重')
    parser.add_argument('--do_predict', action='store_true', help='是否预测未来未见数据')

    # 优化配置
    parser.add_argument('--num_workers', type=int, default=10, help='数据加载线程数')
    parser.add_argument('--itr', type=int, default=3, help='实验重复次数')
    parser.add_argument('--train_epochs', type=int, default=10, help='训练轮数')
    parser.add_argument('--batch_size', type=int, default=32, help='训练批大小')
    parser.add_argument('--patience', type=int, default=3, help='早停法耐心值')
    parser.add_argument('--learning_rate', type=float, default=0.0001, help='优化器学习率')
    parser.add_argument('--des', type=str, default='test', help='实验描述')
    parser.add_argument('--loss', type=str, default='mse', help='损失函数类型')
    parser.add_argument('--lradj', type=str, default='type1', help='学习率调整策略')
    parser.add_argument('--use_amp', action='store_true', help='是否使用混合精度训练', default=False)

    # GPU配置
    parser.add_argument('--use_gpu', type=bool, default=True, help='是否使用GPU')
    parser.add_argument('--gpu', type=int, default=0, help='GPU设备编号')
    parser.add_argument('--use_multi_gpu', action='store_true', help='是否使用多GPU', default=False)
    parser.add_argument('--devices', type=str, default='0,1', help='多GPU设备ID列表')

    args = parser.parse_args()

    args.use_gpu = True if torch.cuda.is_available() and args.use_gpu else False

    if args.use_gpu and args.use_multi_gpu:
        args.dvices = args.devices.replace(' ', '')
        device_ids = args.devices.split(',')
        args.device_ids = [int(id_) for id_ in device_ids]
        args.gpu = args.device_ids[0]

    print('Args in experiment:')
    print(args)

    Exp = Exp_Main

    if args.is_training:
        for ii in range(args.itr):
            # setting record of experiments
            setting = '{}_{}_{}_modes{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_fc{}_eb{}_dt{}_{}_{}'.format(
                args.task_id,
                args.model,
                args.mode_select,
                args.modes,
                args.data,
                args.features,
                args.seq_len,
                args.label_len,
                args.pred_len,
                args.d_model,
                args.n_heads,
                args.e_layers,
                args.d_layers,
                args.d_ff,
                args.factor,
                args.embed,
                args.distil,
                args.des,
                ii)

            exp = Exp(args)  # set experiments
            print('>>>>>>>start training : {}>>>>>>>>>>>>>>>>>>>>>>>>>>'.format(setting))
            exp.train(setting)

            print('>>>>>>>testing : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(setting))
            exp.test(setting)

            if args.do_predict:
                print('>>>>>>>predicting : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(setting))
                exp.predict(setting, True)

            torch.cuda.empty_cache()
    else:
        ii = 0
        setting = '{}_{}_{}_ft{}_sl{}_ll{}_pl{}_dm{}_nh{}_el{}_dl{}_df{}_fc{}_eb{}_dt{}_{}_{}'.format(args.task_id,
                                                                                                      args.model,
                                                                                                      args.data,
                                                                                                      args.features,
                                                                                                      args.seq_len,
                                                                                                      args.label_len,
                                                                                                      args.pred_len,
                                                                                                      args.d_model,
                                                                                                      args.n_heads,
                                                                                                      args.e_layers,
                                                                                                      args.d_layers,
                                                                                                      args.d_ff,
                                                                                                      args.factor,
                                                                                                      args.embed,
                                                                                                      args.distil,
                                                                                                      args.des, ii)

        exp = Exp(args)  # set experiments
        print('>>>>>>>testing : {}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'.format(setting))
        exp.test(setting, test=1)
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
