# -*- coding: utf-8 -*-
"""
https://colab.research.google.com/drive/1YY4BdhhYE6sSNL_A3zg2GegObW35JlQ6
"""

import os
import pathlib

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import scipy.io as sio
from matplotlib import pyplot 
from tensorflow.keras.layers.experimental import preprocessing
from tensorflow.keras import layers
from keras.models import load_model
from tensorflow.keras import models
from tensorflow import keras
import pandas as pd
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import confusion_matrix

MODELS_DIR = 'models/'
if not os.path.exists(MODELS_DIR):
    os.mkdir(MODELS_DIR)
MODEL_TF = MODELS_DIR + 'model'
MODEL_NO_QUANT_TFLITE = MODELS_DIR + 'model_no_quant.tflite'
MODEL_TFLITE = MODELS_DIR + 'model.tflite'
MODEL_TFLITE_MICRO = MODELS_DIR + 'model.cc'


def predict_tflite(tflite_model, x_test):
    # Prepare the test data
  x_test_ = x_test.copy()
  x_test_ = x_test_.reshape((1, x_test.size))
  x_test_ = x_test_.astype(np.float32)

# Initialize the TFLite interpreter
  interpreter = tf.lite.Interpreter(model_content=tflite_model)
  interpreter.allocate_tensors()

  input_details = interpreter.get_input_details()[0]
  output_details = interpreter.get_output_details()[0]

# If required, quantize the input layer (from float to integer)
  input_scale, input_zero_point = input_details["quantization"]
  if (input_scale, input_zero_point) != (0.0, 0):
    x_test_ = x_test_ / input_scale + input_zero_point
    x_test_ = x_test_.astype(input_details["dtype"])
    # Invoke the interpreter

  interpreter.set_tensor(input_details["index"], x_test_)
  interpreter.invoke()
  y_pred = interpreter.get_tensor(output_details["index"])[0]
  
# If required, dequantized the output layer (from integer to float)
  output_scale, output_zero_point = output_details["quantization"]
  if (output_scale, output_zero_point) != (0.0, 0):
    y_pred = y_pred.astype(np.float32)
    y_pred = (y_pred - output_zero_point) * output_scale

  return y_pred


"""#Read training, validation and test data"""

data_train = pd.read_csv(r"G:\code\letter code（q）\train_features(MINE).csv")
data_labels = pd.read_csv(r"G:\code\letter code（q）\train_label(MINE).csv")
data = pd.concat([data_train, data_labels], axis=1)
data = shuffle(data)
print(data.shape)
# print(data.head)

x = data.drop('400', axis=1)
y = data['400']
print(data_train.shape, data_labels.shape)
x_train, x_validate, y_train, y_validate = train_test_split(x, y, test_size=0.20)

y_train = tf.keras.utils.to_categorical(y_train)# , num_classes=4
y_validate = tf.keras.utils.to_categorical(y_validate)
scaler = StandardScaler()
scaler.fit(x_train)
x_train = scaler.transform(x_train)
x_validate = scaler.transform(x_validate)


test_data = pd.read_csv(r"G:\code\letter code（q）\test_features(MINE).csv")
test_label = pd.read_csv(r"G:\code\letter code（q）\test_label(MINE).csv")
test_data = pd.concat([test_data, test_label], axis=1)
x_test = test_data.drop('400', axis=1)
y_test = test_data['400']

# 例如，你可以从 x_train 和 x_validate 中删除额外的特征，以确保输入数据的维度为（None，400）
# x_test_processed = x_test[:, :400]
# x_validate_processed = x_validate[:, :400]



x_test = scaler.transform(x_test)

"""#Create a model"""
model = tf.keras.Sequential()
model.add(layers.Dense(20, activation='relu', input_shape=(400,)))
model.add(layers.Dense(10, activation='softmax'))
# model.add(layers.Dropout(0.15))
model.summary()

"""Fit the model"""

opt = keras.optimizers.Adam(learning_rate=0.001)
model.compile(optimizer=opt, loss=tf.keras.losses.BinaryCrossentropy(), metrics=['accuracy'])

EPOCHS = 500
callbacks = [EarlyStopping(monitor='val_loss', patience=12), ModelCheckpoint(filepath='best_model.h5', monitor='val_loss', save_best_only=True)]  # uses validation set to stop training when it start overfitting
# print(x_train)
# print(y_train)
# print(x_validate)
# print(y_validate)
history = model.fit(x_train, y_train, validation_data=(x_validate, y_validate), epochs=EPOCHS, callbacks=callbacks, batch_size=32, verbose=1, shuffle=True)













model = load_model('./best_model.h5')

# Assuming you have stored accuracy metrics during training
accuracy = history.history['accuracy']
val_accuracy = history.history['val_accuracy']

plt.figure(figsize=(12, 6))

# Plot Loss
plt.subplot(1, 2, 1)
plt.plot(history.epoch, history.history['loss'], history.history['val_loss'], linewidth=7)
plt.legend(['loss', 'val_loss'], fontsize='20')
plt.title('Training and Validation Loss')
plt.ylim([-2, 4])  # 设置纵坐标范围

# Plot Accuracy
plt.subplot(1, 2, 2)
plt.plot(history.epoch, accuracy, val_accuracy, linewidth=7)
plt.legend(['accuracy', 'val_accuracy'], fontsize='20')
plt.title('Training and Validation Accuracy')
plt.ylim([-2, 3])  # 设置纵坐标范围

# Save the plot
plt.savefig('loss_and_accuracy.png')
# plt.show()




# 假设你有训练和验证的损失和准确度数据
data = {
    'Epoch': history.epoch,
    'Training Loss': history.history['loss'],
    'Validation Loss': history.history['val_loss'],
    'Training Accuracy': accuracy,
    'Validation Accuracy': val_accuracy
}

# 创建一个 DataFrame
df = pd.DataFrame(data)

# 将 DataFrame 保存到 CSV 文件
df.to_csv('loss_and_accuracy_data.csv', index=False)


















# model = load_model('./best_model.h5')
# model.save('best_model.h5')
# metrics = history.history
# plt.plot(history.epoch, metrics['loss'], metrics['val_loss'])
# plt.legend(['loss', 'val_loss'])
# plt.show()
# plt.savefig('loss.png')
# print(best_model.h5)

"""Check test accuracy"""

model = load_model('best_model.h5')
# model.save('G:/code/letter code（css）')
y_pred = np.reshape(np.argmax(model.predict(x_test), axis=1), [len(x_test), 1])
print(y_pred)
y_true = np.reshape(y_test.values, [-1, 1])
test_acc = float(sum(y_pred == y_true) / len(y_true))
print('Test accuracy is:')
print(f"{test_acc:.2%}")

converter = tf.lite.TFLiteConverter.from_saved_model(MODEL_TF)
model_no_quant_tflite = converter.convert()


# Save the model to disk
open(MODEL_NO_QUANT_TFLITE, "wb").write(model_no_quant_tflite)


def representative_dataset():
  for i in range(len(x_train)):
    # print(len(x_train))
    yield[x_train[i, :].reshape(1, 400).astype(np.float32)]

# Set the optimization flag.


converter.optimizations = [tf.lite.Optimize.DEFAULT]
# Enforce integer only quantization
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
# Provide a representative dataset to ensure we quantize correctly.
converter.representative_dataset = representative_dataset
model_tflite = converter.convert()

# Save the model to disk
open(MODEL_TFLITE, "wb").write(model_tflite)

(predict_tflite(model_no_quant_tflite, x_test[4, :]))

"""Note depending on the model the quantized version might have higher accuracy. """

# Calculate predictions with full software
y_pred = np.reshape(np.argmax(model.predict(x_test), axis=1), [len(x_test), 1])
test_acc = float(sum(y_pred == y_true) / len(y_true))
print('Test accuracy with model:')
print(f"{test_acc:.2%}")
y_test_pred_no_quant_tflite = np.empty([x_test.shape[0], 1])
y_test_pred_tflite = np.empty([x_test.shape[0], 1])
# Calculate predictions with tensorflow lite
for i in range(0, x_test.shape[0]):
  y_test_pred_no_quant_tflite[i, 0] = np.argmax(predict_tflite(model_no_quant_tflite, x_test[i, :]))

test_acc = float(sum(y_test_pred_no_quant_tflite == y_true) / len(y_true))
print('Test accuracy with model tf lite:')
print(f"{test_acc:.2%}")


# Calculate predictions with tensorflow lite quantized model
for i in range(0, x_test.shape[0]):
  y_test_pred_tflite[i, 0] = np.argmax(predict_tflite(model_tflite, x_test[i, :]))

test_acc = float(sum(y_test_pred_tflite == y_true) / len(y_true))
print('Test accuracy with model quantized:')
print(f"{test_acc:.2%}")


y_test_tflite = {"y_test_pred_tflite": y_test_pred_tflite, "x_test": x_test}
sio.savemat('models/tflite_pred.mat', y_test_tflite)

# Calculate size
size_no_quant_tflite = os.path.getsize(MODEL_NO_QUANT_TFLITE)
size_tflite = os.path.getsize(MODEL_TFLITE)

# Compare size
# Compare size
pd.DataFrame.from_records(
    [["TensorFlow Lite", f"{size_no_quant_tflite} bytes ", f"(reduced by {0} bytes)"],
     ["TensorFlow Lite Quantized", f"{size_tflite} bytes", f"(reduced by {size_no_quant_tflite - size_tflite} bytes)"]],
    columns=["Model", "Size", ""], index="Model")
#
# # Install xxd if it is not available
# !apt-get update && apt-get -qq install xxd
# # Convert to a C source file, i.e, a TensorFlow Lite for Microcontrollers model
# !xxd -i {MODEL_TFLITE} > {MODEL_TFLITE_MICRO}
# # Update variable names
# REPLACE_TEXT = MODEL_TFLITE.replace('/', '_').replace('.', '_')
# !sed -i 's/'{REPLACE_TEXT}'/g_model/g' {MODEL_TFLITE_MICRO}