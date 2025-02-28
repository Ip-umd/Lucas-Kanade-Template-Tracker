import cv2
import glob
import numpy as np
import matplotlib.pyplot as plt
import copy


def adjust_gamma(image, gamma=1.0):
	# build a lookup table mapping the pixel values [0, 255] to
	# their adjusted gamma values
	invGamma = 1.0 / gamma
	table = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
 
	# apply gamma correction using the lookup table
	return cv2.LUT(image, table)

def affineLKtracker(img, tmp, rect, p):
    img = cv2.GaussianBlur(img,(3,3),0)
    tmp = cv2.GaussianBlur(tmp,(3,3),0)
    W = getAffineMat(p)
    normP = 1
    thresh = 0.006
    count = 0
    
#    tmp = cv2.equalizeHist(tmp)
#    cv2.imshow("tmpN",tmp)

    while normP > thresh:
        count+=1
        
        Iw = cv2.warpAffine(img, W, (0, 0), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)        
        Iw = Iw[rect[0,1]:rect[2,1] , rect[0,0]:rect[2,0]]
        
        if np.linalg.norm(Iw) < np.linalg.norm(tmp):
            print("gamma")
            img  = adjust_gamma(img, gamma=1.5)
        
        Ix = cv2.Sobel(np.float32(img), cv2.CV_64F, 1, 0, ksize = 5)
        Iy = cv2.Sobel(np.float32(img), cv2.CV_64F, 0, 1, ksize = 5)

        Ix = cv2.warpAffine(Ix, W, (0, 0), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)
        Iy = cv2.warpAffine(Iy, W, (0, 0), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)
        
        Ix = Ix[rect[0,1]:rect[2,1] , rect[0,0]:rect[2,0]]
        Iy = Iy[rect[0,1]:rect[2,1] , rect[0,0]:rect[2,0]]
        

# =============================================================================
#         Ix = cv2.warpAffine(img, W, (0, 0), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)
#         Ix = Ix[rect[0,1]:rect[2,1] , rect[0,0]:rect[2,0]]
#         
# #        Ix = cv2.equalizeHist(Ix)
# #        cv2.imshow("equ",Ix)        
# 
#         Ix = cv2.Sobel(np.float32(Ix), cv2.CV_64F, 1, 0, ksize = 5)
#         Iy = cv2.Sobel(np.float32(Ix), cv2.CV_64F, 0, 1, ksize = 5)
# =============================================================================
        
        error = tmp.flatten().astype(np.int)-Iw.flatten().astype(np.int)
        
        # Step 4 , Step 5
        xGrid = np.asarray(list(range(Ix.shape[1])))
        yGrid = np.asarray(list(range(Ix.shape[0])))
        
        xGrid , yGrid = np.meshgrid(xGrid, yGrid)
        
        # delIxJ = [Ix*x Iy*x Ix*y Iy*y Ix Iy ]
        steepestImg = np.array([ \
             np.multiply(Ix.flatten(),xGrid.flatten()),
             np.multiply(Iy.flatten(),xGrid.flatten()),
             np.multiply(Ix.flatten(),yGrid.flatten()),
             np.multiply(Iy.flatten(),yGrid.flatten()),
             Ix.flatten(),
             Iy.flatten() \
             ]).T
        H = np.dot(steepestImg.T,steepestImg)
        
        dp = np.dot(np.linalg.pinv(H), np.dot(steepestImg.T, error))        
        
        normP = np.linalg.norm(dp)
        p = p+(dp*10)
        W = getAffineMat(p)

        if(count > 1000):
            break
    print("count : ", count)
    return p

def getAffineMat(p):
    W = np.hstack([np.eye(2),np.zeros((2,1))]) + p.reshape((2,3),order = 'F')
    return W

images = []
imagesColor = []
for file in glob.glob(f"data/car/*.jpg"):
    inputImage = cv2.imread(file)
    grey = cv2.cvtColor(inputImage, cv2.COLOR_BGR2GRAY)
    images.append(grey)
    imagesColor.append(inputImage)
    
# initialization
#rect = np.array([[123,92],[172,92],[172,150],[123,150]])
rect = np.array([[123,104],[336,104],[336,275],[123,275]])
#rect = np.array([[257,292],[285,292],[285,361],[257,361]])
p = np.zeros(6) 
template = images[0][rect[0,1]:rect[2,1] , rect[0,0]:rect[2,0]]
cv2.imshow("mp", template)
rectNew = copy.deepcopy(rect)
out = cv2.VideoWriter('car.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (images[0].shape[1],images[0].shape[0]))
for i in range(1,len(images)):
    print("Frame : " ,i)
    p = affineLKtracker(images[i], template, rect, p)
    
    # Plot new poly
    w = getAffineMat(p)
    rectDraw_ = np.dot(w,np.vstack((rect.T, np.ones((1,4))))).T
    rectTemp = rectDraw_.astype(np.int32)
    [xmax, ymax] = list(np.max(rectTemp, axis = 0).astype(np.int))
    [xmin, ymin] = list(np.min(rectTemp, axis = 0).astype(np.int))
    rectNew=np.array([[xmin,ymin],
                     [xmax,ymin],
                     [xmax,ymax],
                     [xmin,ymax]])
    
#    cv2.imshow("Poly",cv2.polylines(imagesColor[i],[rectTemp],True,(0,255,0),thickness = 5))
    output = cv2.polylines(imagesColor[i],[rectNew],True,(0,255,0),thickness = 5)
    cv2.imshow("Poly",output)
    # plot first poly
    rectTemp = rect.astype(np.int32)
    rectTemp = rectTemp.reshape((-1,1,2))
#    cv2.imshow("Poly",cv2.polylines(imagesColor[i],[rectTemp],True,(255,0,0),thickness = 5))
    
    out.write(output)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break 
out.release()
cv2.waitKey(0)
cv2.destroyAllWindows()