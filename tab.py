import numpy as np
for i in range(1,100):
    a=np.random.rand()*100
    b=np.random.rand()*100
    c=np.random.rand()
    if c<0.25:
        print("%.2f + %.2f = %.2f" %(a,b,a+b))
    if c<0.5 and c>0.25:
        print("%.2f x %.2f = %.2f" %(a,b,a*b))
    if c<0.75 and c>0.5:
        b=b/10
        print("%.2f / %.1f = %.2f" %(a,b,a/b))
    if  c>0.75:
        print("%.2f - %.2f = %.2f" %(a,b,a-b))