# Educational tutorial | Sheima Alameeri, PhD
import numpy as np
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import csv
rng=np.random.default_rng(20261028)
Path('assets').mkdir(exist_ok=True)
plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'font.size':11})
def fit_interval(x,y,z):
    X=np.column_stack([np.ones(len(x)),x]); Z=np.column_stack([np.ones(len(z)),z])
    beta=np.linalg.lstsq(X,y,rcond=None)[0]
    s2=np.sum((y-X@beta)**2)/(len(x)-2)
    h=np.einsum('ij,jk,ik->i',Z,np.linalg.inv(X.T@X),Z)
    q=t.ppf(.975,len(x)-2)
    return Z@beta,q*np.sqrt(s2*h),q*np.sqrt(s2*(1+h))
def save(fig,name):
    fig.text(.5,.015,'Sheima Alameeri, PhD | Prediction Intervals and Coverage',ha='center',fontsize=9,color='#24476b')
    fig.tight_layout(rect=[0,.05,1,1]);fig.savefig('assets/'+name+'.png',dpi=150);plt.close(fig)
x=np.linspace(-1,1,60);z=np.linspace(-1,1,200)
y=1+2*x+rng.normal(0,.5,len(x))
m,ci,pi=fit_interval(x,y,z)
assert np.all(pi>ci)
fig,ax=plt.subplots(figsize=(9,4.5));ax.fill_between(z,m-pi,m+pi,color='#b9d8ef',label='95% prediction interval');ax.fill_between(z,m-ci,m+ci,color='#337fb4',alpha=.6,label='95% confidence interval for mean');ax.plot(z,m,color='#123b64');ax.scatter(x,y,s=15,color='#245a84');ax.set(xlabel='x',ylabel='Response',title='Mean uncertainty versus a future observation');ax.legend();save(fig,'intervals')
# One independent training sample and one future observation per replication.
# This makes Bernoulli MCSE appropriate at each fixed x.
B=4000; points=np.array([-.9,0,.9]); rows=[]
for scenario in ['Correct linear / constant noise','Curved mean / constant noise','Linear mean / changing noise']:
    hits=[];widths=[]
    for b in range(B):
        xx=rng.uniform(-1,1,60)
        mean=lambda v: 1+2*v+(2*v*v if scenario.startswith('Curved') else 0)
        noise=lambda v: .2+.9*(v+1)/2 if scenario.endswith('changing noise') else np.full_like(v,.5)
        yy=mean(xx)+rng.normal(size=len(xx))*noise(xx)
        mm,_,pp=fit_interval(xx,yy,points)
        future=mean(points)+rng.normal(size=3)*noise(points)
        hits.append(np.abs(future-mm)<=pp);widths.append(2*pp)
    h=np.asarray(hits).mean(axis=0);w=np.asarray(widths).mean(axis=0)
    for j,v in enumerate(points):
        se=np.sqrt(h[j]*(1-h[j])/B)
        rows.append([scenario,v,h[j],se,w[j]])
with open('assets/coverage.csv','w') as f:
    writer=csv.writer(f);writer.writerow(['scenario','x','coverage','MCSE','mean_width']);writer.writerows(rows)
fig,axs=plt.subplots(1,2,figsize=(11,4.5))
for k,s in enumerate(sorted(set(r[0] for r in rows))):
    rr=[r for r in rows if r[0]==s]; xx=np.array([r[1] for r in rr])
    ph=np.array([r[2] for r in rr]); zc=1.95996398454; den=1+zc**2/B; cen=(ph+zc**2/(2*B))/den; half=zc*np.sqrt(ph*(1-ph)/B+zc**2/(4*B**2))/den
    axs[0].errorbar(xx,ph,yerr=np.maximum(0,np.vstack([ph-cen+half,cen+half-ph])),capsize=4,fmt='o-',label=s,color=['#123b64','#3986b9','#70b4cc'][k])
    axs[1].plot(xx,[r[4] for r in rr],'o-',label=s,color=['#123b64','#3986b9','#70b4cc'][k])
axs[0].axhline(.95,color='gray',ls='--');axs[0].set(ylabel='Observed coverage',xlabel='Fixed prediction location x',title='Coverage: 95% Wilson intervals',ylim=(.65,1.025))
axs[1].set(ylabel='Mean prediction interval width',xlabel='Fixed prediction location x',title='Width alone cannot establish reliability')

for ax in axs: ax.set_xticks(points)
axs[1].legend(fontsize=8);save(fig,'coverage-and-width')
correct=[r for r in rows if r[0].startswith('Correct')]
assert all(abs(r[2]-.95)<5*r[3] for r in correct)
assert all(np.isfinite(r[4]) and r[4]>0 for r in rows)
print('4000 independent replications per scenario; checks passed.')
for r in rows: print(f'{r[0]} | x={r[1]:.1f}: coverage={r[2]:.4f}, MCSE={r[3]:.4f}, width={r[4]:.3f}')
