import math

CX, CY, R, NR = 250, 232, 150, 44
names = ['SURVEYORS','TAKE-OFF','QUICKS','RODS','MATCHERS']
pts = {}
for i, n in enumerate(names):
    a = math.radians(-90 + 72*i)
    pts[n] = (CX + R*math.cos(a), CY + R*math.sin(a))

def edge(a, b, trim=NR+6):
    (x1,y1),(x2,y2) = pts[a], pts[b]
    dx, dy = x2-x1, y2-y1
    d = math.hypot(dx,dy); ux, uy = dx/d, dy/d
    return (round(x1+ux*trim,1), round(y1+uy*trim,1),
            round(x2-ux*trim,1), round(y2-uy*trim,1))

HARD = [('SURVEYORS','TAKE-OFF'),('TAKE-OFF','QUICKS'),('QUICKS','RODS'),
        ('RODS','MATCHERS'),('RODS','SURVEYORS')]
SOFT = [('MATCHERS','SURVEYORS'),('MATCHERS','TAKE-OFF'),('SURVEYORS','QUICKS'),
        ('TAKE-OFF','RODS'),('QUICKS','MATCHERS')]

parts = []
for a,b in SOFT:
    x1,y1,x2,y2 = edge(a,b)
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#6E6558" stroke-width="1.2" stroke-dasharray="5 5" marker-end="url(#soft)"/>')
for a,b in HARD:
    x1,y1,x2,y2 = edge(a,b)
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#D8B25C" stroke-width="2.4" marker-end="url(#hard)"/>')
for n,(x,y) in pts.items():
    parts.append(f'<circle cx="{round(x,1)}" cy="{round(y,1)}" r="{NR}" fill="#211E19" stroke="#8A8173" stroke-width="1.2"/>')
    parts.append(f'<text x="{round(x,1)}" y="{round(y+3.5,1)}" font-family="IBM Plex Mono, monospace" font-size="10" fill="#E6E1D4" text-anchor="middle" letter-spacing=".5">{n}</text>')

GRAPH = '\n        '.join(parts)
open('_graph.svg','w').write(GRAPH)
print('graph ok')
