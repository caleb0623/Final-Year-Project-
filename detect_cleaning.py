import argparse
import time
from pathlib import Path
import numpy as np
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.Newdatasets import LoadStreams, LoadImages, letterbox
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel


class detect():              #weight path
    def __init__(self,weight='best.pt'):
        self.weights=[weight]
        #self.source='testImage/test.png' #path to image, may be ask caleb to pass in his saved image?
        self.img_size=640
        self.conf_thres=0.5
        self.iou_thres=0.45 
        self.device='' 
        self.view_img=False 
        self.save_txt=True 
        self.save_conf=False 
        self.nosave=False 
        self.classes=None 
        self.agnostic_nms=False 
        self.augment=False 
        self.update=False 
        self.project='myfile' #path to the desired directory
        self.name='test' #name of the desired folder
        self.exist_ok=True #if True, does not create new directory, name2
        self.no_trace=True
        self.weights, self.view_img, self.save_txt, self.imgsz, self.trace =  self.weights, self.view_img, self.save_txt, self.img_size, not self.no_trace
        # self.save_img = not self.nosave and not self.source.endswith('.txt')  
        self.save_img = not self.nosave # save inference images
        # webcam = self.source.isnumeric() or self.source.endswith('.txt') or self.source.lower().startswith(
        #     ('rtsp://', 'rtmp://', 'http://', 'https://'))

        # Directories
        self.save_dir = Path(increment_path(Path(self.project) / self.name, exist_ok=self.exist_ok))  # increment run
        (self.save_dir / 'labels' if self.save_txt else self.save_dir).mkdir(parents=True, exist_ok=True)  # make dir



        # Initialize
        # set_logging()
        self.device = select_device(self.device)
        self.half = self.device.type != 'cpu'  # half precision only supported on CUDA

        # Load model
        self.model = attempt_load(self.weights, map_location=self.device)  # load FP32 model
        self.stride = int(self.model.stride.max())  # model stride
        self.imgsz = check_img_size(self.imgsz, s=self.stride)  # check img_size

        if self.trace:
            self.model = TracedModel(self.model, self.device, self.img_size)

        if self.half:
           self.model.half()  # to FP16

        # Second-stage classifier
        # classify = False
        # if classify:
        #     modelc = load_classifier(name='resnet101', n=2)  # initialize
        #     modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()

        # Set Dataloader
        self.vid_path, self.vid_writer = None, None
        # if webcam:
        #     view_img = check_imshow()
        #     cudnn.benchmark = True  # set True to speed up constant image size inference
        #     dataset = LoadStreams(source, img_size=imgsz, stride=stride)
        # else:
        #   self.dataset = LoadImages(self.source, img_size=self.imgsz, stride=self.stride) #read video and images

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

        # Run inference
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
    #above is pre-processing
    #####################################################################################################
    #here is inference - pack into another function, need to figure out what parameter to be passed in from caleb.
    def inference(self, img0: np):
        ori = img0.copy() #if didn't use .copy, it will only be a pointer to the altered image later
        old_img_w = old_img_h = self.imgsz
        old_img_b = 1
        img = letterbox(img0, self.img_size, stride=self.stride)[0]

        # Convert
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)   

        #for path, img, im0s, vid_cap in self.dataset:
        img = torch.from_numpy(img).to(self.device) #convert to tensor then moves the tensor to the specified device
        img = img.half() if self.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

            # Warmup
        if self.device.type != 'cpu' and (old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
            old_img_b = img.shape[0]
            old_img_h = img.shape[2]
            old_img_w = img.shape[3]
            for i in range(3):
                self.model(img, augment=self.augment)[0]

        # Inference
        with torch.no_grad():   # Calculating gradients would cause a GPU memory leak
            self.pred = self.model(img, augment=self.augment)[0]


    ########################################################################################################
    #post-processing - don't know need to pack together with inference or sendiri satu function
            # Apply NMS - don't know want to indent under with torch.no_grad() or not
            self.pred = non_max_suppression(self.pred, self.conf_thres, self.iou_thres, classes=self.classes, agnostic=self.agnostic_nms)


            # if classify:
            #     pred = apply_classifier(pred, modelc, img, im0s)

            #print("Scanning......\n") this is used to debug whether the algorithm is scanning or not

            if (len(self.pred[0])!=0): #added if detected
                
            # Process detections
                for i, det in enumerate(self.pred):  # detections per image
                    # if webcam:  # batch_size >= 1
                    #     p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
                    # else:
                    # p, s, im0, frame = path, '', im0, getattr(self.dataset, 'frame', 0)
                    s, im0 = '', img0
                    # p = Path(p)  # to Path
                    # save_path = str(self.save_dir / p.name)  # img.jpg
                    # txt_path = str(self.save_dir / 'labels' / p.stem) + ('' if self.dataset.mode == 'image' else f'_{frame}')  # img.txt
                    gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                    if len(det):
                        # Rescale bounding boxes from img_size to im0 size
                        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                        # Print results
                        for c in det[:, -1].unique():
                            n = (det[:, -1] == c).sum()  # detections per class
                            s += f"{n} {self.names[int(c)]}{'s' * (n > 1)} "  # add to string

                        # Write results
                        for *xyxy, conf, cls in reversed(det):
                            # if self.save_txt:  # Write to file
                            #     xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            #     line = (cls, *xywh, conf) if self.save_conf else (cls, *xywh)  # label format
                            #     with open(txt_path + '.txt', 'a') as f:
                            #         f.write(('%g ' * len(line)).rstrip() % line + '\n')

                            if self.save_img or self.view_img:  # Add bbox to image
                                label = f'{self.names[int(cls)]} {conf:.2f}'
                                plot_one_box(xyxy, im0, label=label, color=self.colors[int(cls)], line_thickness=2)

                    # Print 
                    #print(f'{s}') #detected result class in string

                    # Stream results
                    # self.view_img = True
                    # if self.view_img:  #im0 is the detected image with bounding box
                    #     cv2.imshow('image', im0)
                    #     cv2.waitKey(1000)  # 1 millisecond the program will run this code every frame

                    # Save results (image with detections)
                    # if self.save_img:
                    #     # if self.dataset.mode == 'image': #can change something here, make it save the detected object image from
                    #     #     #stream instead of writing it into video using vid_writer
                    #     save_path ="savedImages/student.png"
                    #     cv2.imwrite(save_path, ori)
                    #     print(f" The image with the result is saved in: {save_path}")
                        # else:  # 'video' or 'stream'
                        #     if vid_path != save_path:  # new video else same video then continue writing
                        #         vid_path = save_path
                        #         if isinstance(vid_writer, cv2.VideoWriter):
                        #             vid_writer.release()  # release previous video writer
                        #         if vid_cap:  # video
                        #             fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        #             w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        #             h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        #         else:  # stream
                        #             fps, w, h = 30, im0.shape[1], im0.shape[0]
                        #             save_path += '.mp4' 
                        #             #cv2.VideoWriter(filename, fourcc, fps, frameSize, isColor=True)
                        #         vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        #     vid_writer.write(im0)

                
                #dataset.ori = "Not original"  #It will affect the value of dataset.ori 
                #during execution.
                #command above is to test if we can change the value 
                #of an object properties during execution

                #ask user to continue not (guard revoke or not, can use cv2.waitKey() here)
                # try:
                #     answ = int(input ("Would you like to continue: "))
                #     integrate GUI here and save image here
                # except:
                #     break

                # try:
                #     cv2.waitKey(10) == "j"
                #     # cv2.destroyAllWindows()
                #     print("Yes!!!!!!\n")
                # except:
                #     break

        #may not need to save label        
        # if self.save_txt or self.save_img:
        #     s = f"\n{len(list(self.save_dir.glob('labels/*.txt')))} labels saved to {self.save_dir / 'labels'}" if self.save_txt else ''
            
            #print(f"Results saved to {save_dir}{s}")
                print(f'Done.')
                inference= [s,ori]
                return inference
            




if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--weights', nargs='+', type=str, default='yolov7.pt', help='model.pt path(s)')
    # parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
    # parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    # parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    # parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    # parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    # parser.add_argument('--view-img', action='store_true', help='display results')
    # parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    # parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    # parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    # parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    # parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    # parser.add_argument('--augment', action='store_true', help='augmented inference')
    # parser.add_argument('--update', action='store_true', help='update all models')
    # parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    # parser.add_argument('--name', default='exp', help='save results to project/name')
    # parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    # parser.add_argument('--no-trace', action='store_true', help='don`t trace model')
    # opt = parser.parse_args()
    # print(opt)
    #check_requirements(exclude=('pycocotools', 'thop'))
    detector = detect('best.pt')
    result =''

    pic = cv2.imread('testImage/test.png')
    inference = detector.inference(pic)
    print (inference[0])
    pic = cv2.imread('testImage/short.jpeg')
    inference = detector.inference(pic)
    print (inference[0])
    cv2.imshow('image', inference[1]) #this is used to display the result
    cv2.waitKey(1000) 