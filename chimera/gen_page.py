graph = open('_graph.svg').read()

SCHOOLS = [
 dict(k='matchers', name='Matchers', accent='--brass',
   doc='Carry the library on your chest. 180 known chips, each identified by a count of nicks filed into one edge, read by thumb, in the dark, at a run.',
   src='Carried reagents', top='Flask', stroke='Set',
   good='Turns unfamiliar material into FAST material better than anyone — matching is recognition, and recognition is under a quarter-second.',
   bad='Anything that occupies one hand halves her. Cold and wet finish her outright: the nick-code needs bare fingertips.',
   img='''<circle cx="100" cy="46" r="15" fill="#E6E1D4"/>
     <polygon points="80,66 120,66 126,150 74,150" fill="#E6E1D4"/>
     <rect x="80" y="76" width="40" height="42" fill="#211E19" stroke="#D8B25C" stroke-width="1.5"/>
     <g stroke="#D8B25C" stroke-width="1.4">
       <path d="M84 82 v30 M90 82 v30 M96 82 v30 M102 82 v30 M108 82 v30 M114 82 v30"/></g>
     <path d="M118 82 L168 96" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <path d="M168 88 v16" stroke="#D8B25C" stroke-width="2"/>
     <path d="M82 84 L96 100" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <g stroke="#E6E1D4" stroke-width="7" stroke-linecap="round"><path d="M88 150 v46 M112 150 v46"/></g>
     <text x="100" y="218" font-family="IBM Plex Mono, monospace" font-size="9" fill="#D8B25C" text-anchor="middle" letter-spacing="1">FIST IN HER OWN CHEST</text>'''),

 dict(k='rods', name='Rods', accent='--slate',
   doc='Touch nothing. Read through an instrument you have already read through — and above all through seated metal in the forearm. Their line is <em>nothing on the skin</em>.',
   src='Pre-loaded charges', top='Implant', stroke='Solve',
   good='They own distance and deep extraction. Half the country’s ore is found by a man saying <em>iron at forty feet</em> in good faith.',
   bad='State-blind, and it is not a minor axis. He reads half-set brass as superb brass — and half-set eats instruments, up sixty centimetres of rod, into the port at his wrist.',
   img='''<circle cx="92" cy="46" r="15" fill="#E6E1D4"/>
     <polygon points="72,66 112,66 118,150 66,150" fill="#E6E1D4"/>
     <rect x="70" y="78" width="22" height="12" rx="5" fill="#6FA0B0"/>
     <circle cx="81" cy="84" r="13" fill="none" stroke="#6FA0B0" stroke-width="1.2" opacity=".7"/>
     <circle cx="81" cy="84" r="19" fill="none" stroke="#6FA0B0" stroke-width="1" opacity=".4"/>
     <path d="M110 84 L142 118" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <path d="M144 112 L162 196" stroke="#8A8173" stroke-width="5" stroke-linecap="round"/>
     <circle cx="162" cy="196" r="5" fill="#6FA0B0"/>
     <g stroke="#E6E1D4" stroke-width="7" stroke-linecap="round"><path d="M80 150 v46 M104 150 v46"/></g>
     <text x="100" y="218" font-family="IBM Plex Mono, monospace" font-size="9" fill="#6FA0B0" text-anchor="middle" letter-spacing="1">WORKS A METRE AWAY</text>'''),

 dict(k='surveyors', name='Surveyors', accent='--brass',
   doc='Walk the building days early and leave the lines in it. Then fight in a room where every surface is recognition and every boundary is already down.',
   src='The surveyed building', top='Pool', stroke='Set',
   good='On owned ground, the most dangerous thing alive — and they own the runner, because everyone else’s is a prayer with a direction and hers is a rail.',
   bad='Everything else. Off prepared ground she is the weakest thing in the game, and her library goes stale — damp, frost, a repaint, and the house is strange again.',
   img='''<rect x="10" y="30" width="54" height="120" fill="#9A9184" opacity=".45"/>
     <text x="14" y="26" font-family="IBM Plex Mono, monospace" font-size="8" fill="#9A9184" letter-spacing=".5">HALF-SET</text>
     <ellipse cx="112" cy="176" rx="72" ry="16" fill="#6FA0B0" opacity=".28"/>
     <circle cx="112" cy="54" r="15" fill="#E6E1D4"/>
     <polygon points="92,74 132,74 136,140 88,140" fill="#E6E1D4"/>
     <path d="M92 92 L74 158" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <path d="M132 92 L150 158" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <g stroke="#E6E1D4" stroke-width="7" stroke-linecap="round"><path d="M102 140 v34 M124 140 v34"/></g>
     <path d="M40 166 H196" stroke="#D8B25C" stroke-width="2" stroke-dasharray="8 5"/>
     <text x="100" y="218" font-family="IBM Plex Mono, monospace" font-size="9" fill="#D8B25C" text-anchor="middle" letter-spacing="1">PLANTED ON HER OWN LINE</text>'''),

 dict(k='quicks', name='Quicks', accent='--rust',
   doc='Read the living. Tissue is agony to read cold and trivial to recognise warm — every person is the same seven or eight families, so what varies is <em>state</em>, and state is all she ever measures.',
   src='Her own body', top='Implant', stroke='Set',
   good='The best hands on any field: a break set in nine-tenths of a second and the man gets up. She is who they send when the reach found the gallery crew instead of ore.',
   bad='She must be inside arm’s length, and every soldier alive has already decided not to let her touch them. In a siege she is baggage with good hands.',
   img='''<circle cx="70" cy="52" r="14" fill="#E6E1D4"/>
     <polygon points="52,70 88,70 92,146 48,146" fill="#E6E1D4"/>
     <rect x="56" y="80" width="14" height="18" rx="3" fill="#C05A32"/>
     <path d="M86 88 L146 104" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <g stroke="#E6E1D4" stroke-width="6" stroke-linecap="round"><path d="M60 146 v42 M80 146 v42"/></g>
     <circle cx="172" cy="60" r="13" fill="#8A8173"/>
     <polygon points="156,76 188,76 190,146 154,146" fill="#8A8173"/>
     <path d="M156 92 L128 106" stroke="#8A8173" stroke-width="8" stroke-linecap="round"/>
     <g stroke="#8A8173" stroke-width="6" stroke-linecap="round"><path d="M164 146 v42 M182 146 v42"/></g>
     <path d="M64 96 Q100 84 134 104" stroke="#C05A32" stroke-width="2.5" stroke-dasharray="3 3" fill="none"/>
     <text x="100" y="218" font-family="IBM Plex Mono, monospace" font-size="9" fill="#C05A32" text-anchor="middle" letter-spacing="1">HER LINE, ON HIS SKIN</text>'''),

 dict(k='takeoff', name='Take-off hands', accent='--brass',
   doc='Read from the record. <em>This is a barracks of that vintage, so the door pins are wrought, three to a leaf.</em> Recognition without ever having touched the thing.',
   src='The building itself', top='Flask', stroke='Solve',
   good='Disguise does not touch her — grease, blacking, dazzle-plate buy nothing against a woman who never looked at a surface in her life. The low-acuity grinder’s school.',
   bad='She cannot check. A plausible lie about the vintage is nearly as good as beating her, and her errors always complete, because chained cannot be aborted.',
   img='''<rect x="150" y="20" width="46" height="180" fill="#2A2620"/>
     <g stroke="#D8B25C" stroke-width="1.4" fill="none">
       <circle cx="160" cy="70" r="7"/><circle cx="160" cy="118" r="7"/><circle cx="160" cy="166" r="7"/></g>
     <circle cx="86" cy="46" r="15" fill="#E6E1D4"/>
     <polygon points="66,66 106,66 110,146 62,146" fill="#E6E1D4"/>
     <path d="M106 86 L150 108" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <path d="M66 88 L38 116" stroke="#E6E1D4" stroke-width="8" stroke-linecap="round"/>
     <g stroke="#E6E1D4" stroke-width="7" stroke-linecap="round"><path d="M74 146 v50 M98 146 v50"/></g>
     <path d="M96 34 q22 -6 30 4" stroke="#D8B25C" stroke-width="1.6" fill="none"/>
     <text x="132" y="30" font-family="IBM Plex Mono, monospace" font-size="9" fill="#D8B25C">"one"</text>
     <text x="100" y="218" font-family="IBM Plex Mono, monospace" font-size="9" fill="#D8B25C" text-anchor="middle" letter-spacing="1">MOVING, TALKING, HAND BEHIND</text>'''),
]

cards = []
for s in SCHOOLS:
    cards.append(f'''  <article class="sch" style="--a:var({s['accent']})">
    <figure class="sil">
      <svg viewBox="0 0 200 230" role="img" aria-label="Silhouette of a {s['name'][:-1] if s['name'].endswith('s') else s['name']}."> {s['img']}
      </svg>
    </figure>
    <div class="sbody">
      <h3>{s['name']}</h3>
      <p class="doc">{s['doc']}</p>
      <p class="chips"><span>{s['src']}</span><span>{s['top']}</span><span>{s['stroke']}-led</span></p>
      <p class="gd"><b>Great at</b> {s['good']}</p>
      <p class="bd"><b>Dies to</b> {s['bad']}</p>
    </div>
  </article>''')

open('_cards.html','w').write('\n'.join(cards))
open('_graph_inline.html','w').write(graph)
print('cards ok', len(cards))
