import sys
from random import *
import pygame
import time
from collections import deque
from math import *
from pygame.locals import QUIT,KEYDOWN,K_LEFT,K_RIGHT,K_UP,K_DOWN,Rect,MOUSEBUTTONDOWN,K_SPACE
pygame.init()
FPSCLOCK = pygame.time.Clock()
size=(1200,830)
SURFACE = pygame.display.set_mode(size)
color={
    "black":[0,0,0],
    "white":[255,255,255],
    "red":[255,0,0],
    "blue":[0,0,255],
    "yellow":[255,255,0],
    "green":[0,255,0],
    "gray":[192,192,192]
    }
#angle : - 가 시계방향, + 가 반시계 방향
QE=["white","red","blue","yellow","green","gray"]
colorn=[QE[i%len(QE)]for i in range(100)]

"""
각도를 사용할때 우리가 쓰는 일반 각도를 쓰되, 계산할때는 삼각함수의 각도 사용
"""

def angle_change(angle):
    # -90 : 180, -180 : 270, -91 : 181
    return (-(angle-90))%360

class ball(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.rimg=[pygame.image.load("ball/red.png").convert_alpha(),pygame.image.load("ball/blue.png").convert_alpha()]
        self.size=27 # ball size, 반지름
        self.img=[0,0]
        self.img[0]=pygame.transform.scale(self.rimg[0],(self.size*2,self.size*2))
        self.img[1]=pygame.transform.scale(self.rimg[1],(self.size*2,self.size*2))
        self.mask=[pygame.mask.from_surface(self.img[0]),pygame.mask.from_surface(self.img[1])]
        self.r=90#120, between ball length
        self.x=[size[0]//2,size[0]//2]  # red,blue
        self.y=[size[1]//2,size[1]//2]# red,blue
        self.angle=180
        self.rn=1 # rotation number, 1 : blue rotation, 0 : red rotation
        self.rc=[color["red"],color["blue"]] #rotation color
        self.dn=1 #direction, 1 : right, -1 : left
        self.rect=[self.img[0].get_rect(),self.img[1].get_rect()]
        self.startangle=self.angle
        self.bv=0.5 #0. # angle/tick 단위 시간당 회전 각, ball velocity



    def rotation(self): # 공의 회전
        self.angle-=self.bv*self.dn
        self.angle%=360
            
    def draw(self): # Rotation Number 를 반대 ball 의 위치에서 angle 에 따라 회전
        Rn=self.rn
        self.x[Rn]=self.x[(Rn+1)%2]+self.r*sin(radians(self.angle))
        self.y[Rn]=self.y[(Rn+1)%2]+self.r*cos(radians(self.angle))
        #print("##",self.x[(Rn+1)%2],self.y[(Rn+1)%2])
        #print("##",self.x[Rn],self.y[Rn])

        self.rect[0].center=(self.x[0],self.y[0])
        self.rect[1].center=(self.x[1],self.y[1])


        SURFACE.blit(self.img[0],self.rect[0])
        SURFACE.blit(self.img[1],self.rect[1])

    def afterimage(self,cnt): # 공의 잔상
        Rn=self.rn
        for i in range(cnt):
            img=self.rimg[Rn]
            S=self.size*2-(self.size*2/(2*cnt))*(i+1)
            img=pygame.transform.scale(img,(S,S))
            img.set_alpha(256-(i+1)*(246/cnt))
            rect=img.get_rect()
            na=2*(40/cnt)*(i+1)#*self.bv
            if self.startangle!=inf:
                AIA=-inf
                # 잔상과 본체간의 각의 크기를 구해서 뒤로 빠지지 않는가 구분한뒤 그리기
                # 시계방향, 반시계 방향으로 코드를 구현후 둘의 규칙을 찾아서 하나로 만듬
                if self.dn*self.startangle<self.dn*self.angle:
                    AIA=360-self.dn*(self.angle-self.startangle)
                else:
                    AIA=self.dn*(self.startangle-self.angle)
                if AIA<=na:
                    break
            X=self.x[(Rn+1)%2]+self.r*sin(radians(self.angle+self.dn*na))
            Y=self.y[(Rn+1)%2]+self.r*cos(radians(self.angle+self.dn*na))
            if(i+1==cnt):self.startangle=inf

            rect.center=(X,Y)
            SURFACE.blit(img,rect)
            
    def check(self,pos):
        Rn=self.rn
        k=sqrt(abs(self.x[Rn]-pos[0])**2+abs(self.y[Rn]-pos[1])**2)
        #print(self.x[Rn],self.y[Rn])
        #print(k,self.size)
        if k<=self.size*2:
            self.x[Rn]=pos[0]
            self.y[Rn]=pos[1]
            self.change()
            return 1
        return 0

    def change(self):
        self.rn+=1
        self.rn%=2
        self.angle+=180
        self.angle%=360
        self.startangle=self.angle

class tile(pygame.sprite.Sprite):
    def __init__(self,bs,ts):
        pygame.sprite.Sprite.__init__(self)
        # bs = ball size, ts = tile size
        self.rimg=[pygame.image.load("tile/change.png").convert_alpha()]
        self.size=27
        self.img=[0,0,0]
        self.img[0]=pygame.transform.scale(self.rimg[0],(self.size*2,self.size*2))
        self.mask=[pygame.mask.from_surface(self.img[0])]

        self.nt=1
        self.bs=bs
        self.ts=ts
        self.t_d=deque([])  # [degree,opt]
        #opt = 0 : x , opt = 1 : change, opt = 2 : fast, opt = 3 : slow
        self.t_s=deque([])  # 타일의 왼쪽 벽의 중심 좌표(A), 타일 자체의 중심 좌표(B), 타일의 오른쪽 벽의 중심 좌표(C)
        self.start=[0,(size[0]/2,size[1]/2)] # [degree(초기 각도),pos(x,y)], 중심에서 타일의 길이만큼 이동: self.ts/2
        self.build()

    def build(self,degree=-1,opt=0): #상대 각도
        #ldg-180+degree = 끝 타일 각도
        # lpos : last pos
        # ldg : last degree
        if degree==-1:
            ldg=self.start[0]
            lpos=self.start[1]
            degree=180
        else:
            ldg=self.t_d[len(self.t_d)-1][0]
            lpos=self.t_s[len(self.t_s)-1][1]
        B=lpos # last pos
        A=(B[0]+self.ts/2*cos(radians(angle_change(ldg))),B[1]+self.ts/2*sin(radians(angle_change(ldg)))) # 타일의 끝부분
        Dg=ldg+degree
        Dg%=360
        C=(B[0]+self.ts/2*sin(radians(angle_change(Dg))),B[1]+self.ts/2*cos(radians(angle_change(Dg)))) # 타일의 끝부분
        self.t_d.append([Dg,opt])
        self.t_s.append([A,B,C])

    def draw(self):
        n=min(5,len(self.t_s))
        for ui in range(n):
            i=n-ui-1
            A=self.t_s[i][0]
            B=self.t_s[i][1]
            C=self.t_s[i][2]
            #pygame.draw.line(SURFACE,color[colorn[i]],A,B,3)
            #pygame.draw.line(SURFACE,color[colorn[i]],B,C,3)
            pygame.draw.circle(SURFACE,color[colorn[i]],B,self.bs+8,6)
            Q=f(A,B,self.bs+5)#32 = bs+5
            QQ=f(B,C,self.bs+5)
            pygame.draw.polygon(SURFACE, color[colorn[i]], Q,6)
            pygame.draw.polygon(SURFACE, color[colorn[i]], QQ,6)
            pygame.draw.circle(SURFACE,color["black"],B,self.bs+5)
            #pygame.draw.polygon(SURFACE, color["black"], Q)
            #pygame.draw.polygon(SURFACE, color["black"], QQ)
            if self.t_d[i][1]!=0:
                ir=self.img[self.t_d[i][1]-1].get_rect()
                ir.center=B
                SURFACE.blit(self.img[self.t_d[i][1]-1],ir)


def f(A,B,r=5):# 두 점을 중선으로 두는 직사각형 만들기
    if B[1]-A[1]==0:
        ans=[(A[0],A[1]-r),(A[0],A[1]+r),(B[0],B[1]+r),(B[0],B[1]-r)]
        return ans
    if B[0]-A[0]==0:
        ans=[(A[0]-r,A[1]),(A[0]+r,A[1]),(B[0]+r,B[1]),(B[0]-r,B[1])]
        return ans

    aa=-(B[1]-A[1])/(B[0]-A[0])
    K=sqrt(abs(A[0]-B[0])**2+abs(A[1]-B[1])**2)
    C=r
    # k : C = abs(A[0]-B[0]) : X_y
    # k : C = abs(A[1]-B[1]) : X_x
    X_y = C*abs(A[0]-B[0])/K
    X_x = C*abs(A[1]-B[1])/K
    ans=[(A[0]-X_x,A[1]-(aa/abs(aa))*X_y),(A[0]+X_x,A[1]+(aa/abs(aa))*X_y),(B[0]+X_x,B[1]+(aa/abs(aa))*X_y),(B[0]-X_x,B[1]-(aa/abs(aa))*X_y)]

    return ans
    #a*b=-1, b=-1/a // y=bx+c, A[1]=b*A[0]+c, A[1]-b*A[0]=c

def start():
    B=ball()
    B.r=100
    B.dn*=-1

    Te=tile(B.size,B.r)
    #Te.build(120)
    #Te.build(300)
    #Te.build(180)
    Te.build(180)
    for i in range(20):
        Te.build(180,1)#randint(1,3))
        Te.build(36,1)#randint(1,3))#randint(1,360))
    Te.build(180)
    Te.build(180)
    print(Te.t_d)
    ###s
    #print(Te.t_d)


    while 1:
        SURFACE.fill(color["gray"])
        key=0
        for event  in pygame.event.get():
            if event.type==QUIT:pygame.quit();sys.exit()
            elif event.type==KEYDOWN:key=event.key
            if key!=0:#==K_SPACE or pygame.mouse.get_pressed()[0]!=0 or pygame.mouse.get_pressed()[2]!=0:
                #print("SDF")
                #opt = 0 : x , opt = 1 : change, opt = 2 : fast, opt = 3 : slow
                if B.check(Te.t_s[1][1])==1:
                    if Te.t_d[1][1]==1:
                        B.dn*=-1
                    elif Te.t_d[1][1]==2:
                        #print("SDFSD")
                        B.bv*=1.05
                    elif Te.t_d[1][1]==3:
                        #print("XCXC")
                        B.bv*=0.95
                    Te.t_s.popleft()
                    Te.t_d.popleft()
                else:
                    print("miss")
                    return
                #B.change()
                #B.dn*=-1
                break
                

        Te.draw()

        B.rotation()
        B.afterimage(10)
        B.draw()
        #FPSCLOCK.tick(50)

        pygame.display.update()

while 1:
    start()
