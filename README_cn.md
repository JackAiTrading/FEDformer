# FEDformer (ICML 2022 论文)

Tian Zhou, Ziqing Ma, Qingsong Wen, Xue Wang, Liang Sun, Rong Jin，《FEDformer：用于长期时间序列预测的频率增强分解Transformer》，发表于第39届国际机器学习会议（ICML 2022），美国马里兰州巴尔的摩，2022年7月17-23日

频率增强分解Transformer（FEDformer）比标准Transformer更高效，具有线性的序列长度复杂度[[论文](https://arxiv.org/abs/2201.12740)]。

我们在六个基准数据集上的实验表明，与最先进的方法相比，FEDformer可以将多元和单变量时间序列的预测误差分别降低14.8%和22.6%。

## 频率增强注意力机制
|![Figure1](https://user-images.githubusercontent.com/44238026/171341166-5df0e915-d876-481b-9fbe-afdb2dc47507.png)|
|:--:| 
| *图1. FEDformer整体结构* |

|![image](https://user-images.githubusercontent.com/44238026/171343471-7dd079f3-8e0e-442b-acc1-d406d4a3d86a.png) | ![image](https://user-images.githubusercontent.com/44238026/171343510-a203a1a1-db78-4084-8c36-62aa0c6c7ffe.png)
|:--:|:--:|
| *图2. 频率增强模块（FEB）* | *图3. 频率增强注意力机制（FEA）* |


## 主要结果
![image](https://user-images.githubusercontent.com/44238026/171345192-e7440898-4019-4051-86e0-681d1a28d630.png)


## 快速开始

1. 安装Python>=3.8和PyTorch 1.9.0
2. 下载数据集。可从[[Autoformer](https://github.com/thuml/Autoformer)]或[[Informer](https://github.com/zhouhaoyi/Informer2020)]获取全部六个基准数据集
3. 训练模型。我们在`./scripts`目录下提供了所有基准测试的实验脚本，分别运行以下命令复现多元和单变量实验结果：

```bash
bash ./scripts/run_M.sh
bash ./scripts/run_S.sh
```


## 引用

如果使用本代码，请引用我们的论文：

```
@inproceedings{zhou2022fedformer,
  title={{FEDformer}: Frequency enhanced decomposed transformer for long-term series forecasting},
  author={Zhou, Tian and Ma, Ziqing and Wen, Qingsong and Wang, Xue and Sun, Liang and Jin, Rong},
  booktitle={Proc. 39th International Conference on Machine Learning (ICML 2022)},
  location = {Baltimore, Maryland},
  pages={},
  year={2022}
}
```

## 扩展阅读
时间序列Transformer综述：

文青松、田舟、张超立、陈伟琦、马子卿、严俊驰、孙亮，《时间序列中的Transformer模型综述》，arXiv预印本 arXiv:2202.07125 (2022)。[论文](https://arxiv.org/abs/2202.07125)


## 联系方式

如有任何问题或需要使用代码，请联系 tian.zt@alibaba-inc.com 或 maziqing.mzq@alibaba-inc.com。

## 致谢

我们感谢以下开源项目提供有价值的代码库和数据集：

https://github.com/thuml/Autoformer

https://github.com/zhouhaoyi/Informer2020

https://github.com/zhouhaoyi/ETDataset

https://github.com/laiguokun/multivariate-time-series-data