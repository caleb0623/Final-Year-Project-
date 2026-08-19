# 🎓 Attire Checker System

> **AI-Powered Student Identification & Attire Monitoring System**

An AI-powered student monitoring and attire verification system developed as a **Final Year Project at Tunku Abdul Rahman University of Management and Technology (TARUMT)**.

The system combines **LBPH face recognition**, **YOLOv7 object detection**, **Firebase**, and an **Android application** to identify students, monitor attire, manage student records, and generate reports.

---

## 📌 Project Overview

The Attire Checker System was designed to assist campus security personnel and administrators in monitoring students through computer vision and automated processing.

The system integrates multiple technologies into a single workflow:

```
                         ┌────────────────────┐
                         │    Camera Input    │
                         └─────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
           ┌─────────────────┐           ┌─────────────────┐
           │      LBPH       │           │     YOLOv7      │
           │ Face Recognition│           │ Attire Detection│
           └────────┬────────┘           └────────┬────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Student & Attire   │
                         │ Verification       │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │      Firebase      │
                         │ Data Synchronizing │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Android / Admin    │
                         │ Application        │
                         └────────────────────┘
						 
```
						 
✨ Main Features
- 👤 Real-time face recognition
- 🧠 AI-based attire detection
- 🎯 Student identification
- 👕 Automated attire verification
- ☁️ Firebase data synchronization
- 📱 Android monitoring application
- 📊 Administrative reporting
- 👨‍🎓 Student record management
- 🔐 Security personnel management
- 📅 Historical record tracking
- 📷 Face registration through camera or gallery				

🛠️ Technology Stack
```table
| Category           | Technologies                   |
| Programming        | Python                         |
| Computer Vision    | OpenCV, LBPH                   |
| Object Detection   | YOLOv7                         |
| Machine Learning   | PyTorch, TorchVision           |
| Cloud & Storage    | Firebase, Google Cloud Storage |
| Mobile Development | Android, Kotlin                |
| Database           | Firebase                       |
| UI / Desktop       | Tkinter                        |
| Email              | Yagmail                        |
| Utilities          | TkCalendar                     |
```
---
🤖 AI & Computer Vision

# 1. LBPH Face Recognition

The system uses LBPH (Local Binary Patterns Histograms) for student face recognition.

LBPH is responsible for identifying registered students from camera input.

## Face Recognition Workflow	

```text

Camera
   │
   ▼
Capture Face
   │
   ▼
Detect Face
   │
   ▼
LBPH Recognition
   │
   ▼
Identify Student
   │
   ▼
Retrieve Student Information

```
Administrators can register student faces using either a camera or existing images.

Face Registration Methods
- 📷 Camera registration
- 🖼️ Gallery registration
- 🆔 Student ID association
- 🧠 Face model training
---

# 2. YOLOv7 Attire Detection

The attire detection component uses YOLOv7, a real-time object detection framework.

YOLOv7 is used as the computer vision component responsible for detecting relevant attire objects from camera input.

The system combines the face recognition and attire detection components to associate an identified student with the corresponding attire detection result.

## Detection Workflow

```
Camera Feed
     │
     ├───────────────┐
     │               │
     ▼               ▼
   LBPH            YOLOv7
     │               │
     ▼               ▼
Student ID       Attire Objects
     │               │
     └───────┬───────┘
             │
             ▼
      Attire Evaluation
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
   Compliant    Violation
       │           │
       └─────┬─────┘
             ▼
          Firebase
```
		  
> **Note: YOLOv7 is an open-source object detection framework. This project integrates and applies YOLOv7 as part of the attire detection component rather than developing the YOLOv7 architecture itself.**
---
# 🧠 YOLOv7

This project uses the YOLOv7 implementation from the original research project:

## YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors

## Original Repository

https://github.com/WongKinYiu/yolov7

## Research Paper

https://arxiv.org/abs/2207.02696

YOLOv7 provides real-time object detection capabilities and supports training and fine-tuning using custom datasets.

---
# 📦 Installation
## Requirements

It is recommended to use Anaconda to manage the Python environment.

Open Anaconda Prompt and install the required Python libraries.

## Python Dependencies

```
pip install Pillow
pip install tkcalendar
pip install --upgrade google-cloud-storage
pip install --upgrade firebase-admin
pip3 install pyrebase4
pip install opencv-contrib-python
pip install yagmail
pip install torch
pip install torchvision
pip install torchaudio
```

or run
```
pip install -r requirements.txt
```
---
# 🏗️ System Architecture
```
                     ATTIRE CHECKER SYSTEM
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
      Face Recognition                  Attire Detection
             │                                 │
             ▼                                 ▼
           LBPH                              YOLOv7
             │                                 │
             └────────────────┬────────────────┘
                              │
                              ▼
                     Student Verification
                              │
                              ▼
                          Firebase
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          Admin System              Android App
                 │                         │
                 ▼                         ▼
            Reporting               Student Records
```
---
# 📁 Suggested Project Structure
```
Attire-Checker-System/
│
├── face/
│   └── Student face images
│
├── model/
│   └── Trained models
│
├── face_recognition/
│   └── LBPH implementation
│
├── attire_detection/
│   └── YOLOv7 implementation
│
├── android/
│   └── TARUMT Android Application
│
├── reports/
│   └── Generated reports
│
├── requirements.txt
│
└── README.md
```
---
# 🧪 YOLOv7 Usage

The original YOLOv7 implementation supports image and video inference.
## Image Inference
```
python detect.py \
    --weights yolov7.pt \
    --conf 0.25 \
    --img-size 640 \
    --source inference/images/horses.jpg
```

## Video Inference
```
python detect.py \
    --weights yolov7.pt \
    --conf 0.25 \
    --img-size 640 \
    --source yourvideo.mp4
```

The actual model, weights, dataset, and configuration used by this project may differ from the original YOLOv7 example.

# 🎯 YOLOv7 Training

YOLOv7 supports training and fine-tuning using custom datasets.

## Example Custom Dataset Training
```
python train.py \
    --workers 8 \
    --device 0 \
    --batch-size 32 \
    --data data/custom.yaml \
    --img 640 640 \
    --cfg cfg/training/yolov7-custom.yaml \
    --weights yolov7_training.pt \
    --name yolov7-custom
```
Training configuration depends on the dataset and model configuration used for the project.
---
# 🧩 Key Technical Components
## LBPH

Local Binary Patterns Histograms (LBPH) is used for face recognition and student identification.

The system allows administrators to register student faces and subsequently recognize them through camera input.

## YOLOv7

YOLOv7 is used for real-time object detection as part of the attire monitoring component.

## Firebase

Firebase provides cloud-based data synchronization between the system components and the Android application.

## OpenCV

OpenCV provides the computer vision functionality required for image and video processing.

## PyTorch

PyTorch supports the machine learning components used by the YOLOv7 detection pipeline.

## Android

The Android application provides lecturers and administrators with access to student-related records and management functions.
---
# 🌟 Project Highlights
```
| Feature                  | Description                        |
| ------------------------ | ---------------------------------- |
| 👤 Face Recognition      | LBPH-based student identification  |
| 👕 Attire Detection      | YOLOv7-based real-time detection   |
| 📷 Face Registration     | Camera and gallery registration    |
| ☁️ Cloud Synchronization | Firebase integration               |
| 📱 Mobile Application    | Android monitoring application     |
| 📊 Reporting             | Date-based report generation       |
| 👨‍🎓 Student Management    | Student records and history        |
| 👮 Security Management   | Security account management        |
| 🔐 Authentication        | User login and password recovery   |
| 📜 History               | Historical student record tracking |
```
---
# 🔬 Project Scope
```
The project demonstrates the integration of:

Computer Vision
       +
Machine Learning
       +
Cloud Services
       +
Mobile Development
       +
Database Management
       +
User Management
       +
Reporting
```
The combination of these technologies creates a complete application ecosystem rather than an isolated machine learning model.
---
# 📚 Research & Development

This project was developed as a Final Year Project and involved research, system design, software development, AI integration, database integration, testing, and application development.

The project demonstrates practical experience in:

- Computer vision
- Face recognition
- Object detection
- Machine learning
- Mobile application development
- Cloud integration
- Database management
- Software engineering
- System integration
- User interface development

---
# ⭐ Project Summary

> **An AI-powered campus monitoring system combining LBPH face recognition and YOLOv7-based attire detection with Firebase synchronization and an Android application.**

The project demonstrates the practical application of AI, computer vision, cloud services, mobile development, and software engineering to solve a real-world monitoring problem.