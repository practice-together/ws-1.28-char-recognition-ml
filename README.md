# ESP32 Touch-Based Character Recognition

A machine learning system for recognizing hand-drawn characters on an ESP32 device with a touch screen display. The system uses a compact CNN model trained on touch input data and runs real-time inference on the Waveshare ESP32-S3 1.28 Touch LCD board.

## Overview

This project demonstrates how to:
- Collect touch input data from an ESP32 touch screen
- Process and convert touch coordinates into training data
- Train a lightweight CNN model suitable for microcontrollers
- Deploy and run inference on the ESP32
- Display predictions on the LCD screen

## Hardware Requirements
- Waveshare ESP32-S3 board with touch LCD
- Computer that can run tensorflow

## Model Architecture

The CNN model uses a compact architecture optimized for microcontrollers:
- Input: 32x32 grayscale images
- 2 convolutional layers (8 and 16 filters)
- 2 max pooling layers
- Dense layer with 32 units
- Output: 5 classes (B, L, I, T, Z)

## Performance

- Model Size: ~140KB
- Inference Time: ~100ms
- Test Accuracy: ~95%

## Acknowledgments

- TensorFlow Lite Micro team
- Waveshare ESP32 team
- Contributors to the MicroTFLite library
- Note: GPT was used to enhance the readability of the code
