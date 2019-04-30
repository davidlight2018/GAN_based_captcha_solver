# 基于GAN的验证码破解
![sample](sample.jpg)

本项目是对暗网Dream Market的验证码进行破解，并实现自动登陆爬取功能。

模型上主要参考了这篇[SimGAN-Captcha](https://github.com/rickyhan/SimGAN-Captcha)。

## 简介(Introduction)
|Name|Description|
|:-:|:-:|
|preprocess.ipynb|预处理，提取方框内的验证码|
|fine-tuned.ipynb|模型训练|
|data-augment.ipynb|数据增强|
|auto_login.py|自动登录程序|

## 预处理(Preprocess)
使用OpenCV的HoughLines去识别框框的直线，进一步作分割。但是这一步其实会有部分损失，因为I、H、d等字符也是存在竖线的，如果严格一些去做切割的话，大概会有5%的损失。但是相比于另两种BoundingRect和ConvexHull方法，这个方法的成功率最高。

## 模型(Model)
具体的模型就不在这介绍了，感兴趣的去看上面那篇。

大概的思路是，使用OpenCV生成验证码，SimGAN对验证码在像素级别上进行修改并训练，使得判别器(Discriminator)无法区分生成的验证码与真实验证码，最后用数据增强(data augmentation)的方式增加真实验证码的训练数据，并用迁移训练(transfer learning)对生成的模型进行调优。最后能够达到整体验证码正确率大于90%，单个字符正确率大于97%的效果。

这里要解释三点：
1. 因为我们的验证码生成方式是比较随意的，即我是肉眼去挑相似的字体，然后扭曲、旋转、扰动等也都是简单的添加的。所以如果直接把这些验证码丢给SimGAN去训练，最后的效果是很差的，总体的准确率大概只有5%。
2. 正确的做法应该是用网格搜索的方式去找最接近目标验证码的生成器，然后生成的验证码能骗过判别器95%以上。然而这部分实验我并没有成功。一是这部分相当的耗时，二是常常训练的判别器过强或过弱，这部分的度我还没有把握好。
3. 所以我通过加入数据增强的方式对模型进行迁移训练。我标注了3000张图片(使用我自己写的[工具](https://github.com/davidlight2018/captcha-label-tool))，并通过数据增强增加到了150000张。然后固定模型的前几层，对后几层继续训练。最后可以达到的效果已经非常不错。
