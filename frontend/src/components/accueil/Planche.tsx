import type { CSSProperties, SVGProps } from "react";

/** Un trait d'encre qui se dessine : `at` = départ (s), `t` = durée (s). */
function T({ at, t = 0.8, ...p }: SVGProps<SVGPathElement> & { at: number; t?: number }) {
  return <path pathLength={1} className="trait" fill="none" stroke="var(--encre)" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round"
    style={{ "--d": `${at}s`, "--t": `${t}s` } as CSSProperties} {...p} />;
}
/** Un aplat (encre, couleur ou trame) qui se pose une fois le trait tracé. */
function A({ at, ...p }: SVGProps<SVGPathElement> & { at: number }) {
  return <path className="aplat" style={{ "--d": `${at}s` } as CSSProperties} {...p} />;
}
const delai = (at: number) => ({ "--d": `${at}s` }) as CSSProperties;

// Cases de la planche (x, y, largeur, hauteur)
const C1 = "M14,14 H386 V178 H14 Z";
const C2 = "M14,192 H193 V392 H14 Z";
const C3 = "M207,192 H386 V392 H207 Z";
const C4 = "M14,406 H386 V586 H14 Z";

// Lignes de vitesse de la case 3, en étoile autour du point d'impact
const vitesse = Array.from({ length: 22 }, (_, i) => {
  const a = (i / 22) * Math.PI * 2 + 0.12;
  const r1 = 34 + (i % 3) * 8, r2 = 150;
  const cx = 296, cy = 292;
  return `M${(cx + Math.cos(a) * r1).toFixed(1)},${(cy + Math.sin(a) * r1).toFixed(1)} L${(cx + Math.cos(a) * r2).toFixed(1)},${(cy + Math.sin(a) * r2).toFixed(1)}`;
});

/**
 * Planche de manga dessinée sous les yeux du visiteur : cadres, décor, personnage, trames, bulle.
 * Illustration originale, en SVG pur. Environ 5 s, une seule fois ; immédiate si l'animation est réduite.
 */
export function PlancheAnimee({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 400 600" className={className} role="img" aria-label="Une planche de manga qui se dessine : une ville au soleil levant, une héroïne déterminée, un impact, et la bulle « Et si ton idée devenait un manga ? »">
      <defs>
        <pattern id="trame" width="8" height="8" patternUnits="userSpaceOnUse">
          <circle cx="4" cy="4" r="1.6" fill="var(--encre)" />
        </pattern>
        <pattern id="trame-fine" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="var(--encre)" strokeWidth="1.2" />
        </pattern>
        <clipPath id="c1"><path d={C1} /></clipPath>
        <clipPath id="c2"><path d={C2} /></clipPath>
        <clipPath id="c3"><path d={C3} /></clipPath>
      </defs>

      {/* La feuille */}
      <rect x="0" y="0" width="400" height="600" fill="var(--blanc, #fff)" />

      {/* 1. Les cadres se tracent */}
      <T at={0} t={0.7} d={C1} strokeWidth={4} />
      <T at={0.25} t={0.6} d={C2} strokeWidth={4} />
      <T at={0.45} t={0.6} d={C3} strokeWidth={4} />
      <T at={0.65} t={0.7} d={C4} strokeWidth={4} />

      {/* 2. Case 1 : la ville au soleil levant */}
      <g clipPath="url(#c1)">
        <A at={1.4} d="M330,56 m-30,0 a30,30 0 1,0 60,0 a30,30 0 1,0 -60,0" fill="var(--soleil)" />
        <T at={1.1} t={0.6} d="M330,56 m-30,0 a30,30 0 1,0 60,0 a30,30 0 1,0 -60,0" />
        <A at={2.1} d="M14,178 V124 H44 V104 H74 V132 H98 V88 H128 V126 H152 V112 H186 V142 H212 V96 H242 V72 H264 V96 H292 V122 H322 V106 H352 V136 H386 V178 Z" fill="url(#trame)" opacity="0.55" />
        <T at={1.2} t={1.2} d="M14,124 H44 V104 H74 V132 H98 V88 H128 V126 H152 V112 H186 V142 H212 V96 H242 V72 H264 V96 H292 V122 H322 V106 H352 V136 H386" />
        <T at={1.9} t={0.4} d="M108,100 v8 M118,100 v8 M108,114 v8 M118,114 v8 M250,84 v8 M250,98 v8 M222,110 v8 M232,110 v8" strokeWidth={2.5} />
        <T at={1.7} t={0.5} d="M56,52 q8,-9 16,0 q8,-9 16,0 M98,36 q6,-7 12,0 q6,-7 12,0" strokeWidth={2.5} />
      </g>

      {/* 3. Case 2 : l'héroïne */}
      <g clipPath="url(#c2)">
        <A at={2.6} d="M14,192 H193 V392 H14 Z" fill="url(#trame-fine)" opacity="0.18" />
        <T at={2.2} t={0.7} d="M60,288 Q60,346 104,364 Q148,346 148,288" />
        <A at={3.1} d="M52,296 L58,250 L44,232 L72,238 L74,210 L94,232 L106,202 L116,232 L138,210 L136,240 L162,232 L150,258 L156,298 Q142,268 120,262 L110,280 L98,262 Q74,266 52,296 Z" fill="var(--encre)" />
        <T at={2.4} t={0.9} d="M52,296 L58,250 L44,232 L72,238 L74,210 L94,232 L106,202 L116,232 L138,210 L136,240 L162,232 L150,258 L156,298 Q142,268 120,262 L110,280 L98,262 Q74,266 52,296 Z" />
        <T at={2.9} t={0.3} d="M70,290 L94,295 M114,295 L138,290" strokeWidth={4} />
        <A at={3.3} d="M74,304 Q84,296 94,304 Q92,320 84,322 Q76,320 74,304 Z M114,304 Q124,296 134,304 Q132,320 124,322 Q116,320 114,304 Z" fill="var(--encre)" />
        <T at={3.0} t={0.4} d="M74,304 Q84,296 94,304 Q92,320 84,322 Q76,320 74,304 Z M114,304 Q124,296 134,304 Q132,320 124,322 Q116,320 114,304 Z" strokeWidth={2.5} />
        <A at={3.45} d="M86,306 m-3,0 a3,3 0 1,0 6,0 a3,3 0 1,0 -6,0 M126,306 m-3,0 a3,3 0 1,0 6,0 a3,3 0 1,0 -6,0" fill="#fff" />
        <T at={3.2} t={0.3} d="M98,342 Q104,346 110,342" strokeWidth={2.5} />
        <A at={3.5} d="M68,362 Q104,382 140,362 L148,392 L60,392 Z" fill="var(--vermillon)" />
        <T at={3.3} t={0.5} d="M68,362 Q104,382 140,362" />
      </g>

      {/* 4. Case 3 : l'impact */}
      <g clipPath="url(#c3)">
        <T at={3.4} t={0.35} d={vitesse.join(" ")} strokeWidth={2} />
        <g className="vibre" style={delai(3.9)}>
          <path d="M296,250 L308,276 L338,268 L318,292 L342,314 L310,310 L300,340 L288,312 L256,318 L276,294 L252,270 L284,276 Z"
            fill="var(--soleil)" stroke="var(--encre)" strokeWidth="3" strokeLinejoin="round" />
          <text x="297" y="301" textAnchor="middle" fontFamily="var(--font-bangers)" fontSize="26" fill="var(--encre)">ZAP!</text>
        </g>
      </g>

      {/* 5. Case 4 : la bulle */}
      <A at={4.0} d={C4} fill="url(#trame)" opacity="0.12" />
      <g className="pop" style={delai(4.2)}>
        <path d="M200,428 C300,428 356,452 356,490 C356,528 300,552 200,552 C176,552 154,550 136,546 L84,574 L104,536 C64,526 44,510 44,490 C44,452 100,428 200,428 Z"
          fill="var(--bulle)" stroke="var(--encre)" strokeWidth="3" strokeLinejoin="round" />
        <text x="200" y="482" textAnchor="middle" fontFamily="var(--font-display)" fontSize="22" fill="var(--encre)">Et si ton idée</text>
        <text x="200" y="514" textAnchor="middle" fontFamily="var(--font-display)" fontSize="22" fill="var(--vermillon)">devenait un manga ?</text>
      </g>
    </svg>
  );
}

/** Traits d'esquisse en fond d'en-tête : le « papier peint » qui se couvre d'encre. */
export function Esquisses({ className }: { className?: string }) {
  const s = (at: number, t = 2.2) => ({ "--d": `${at}s`, "--t": `${t}s` }) as CSSProperties;
  return (
    <svg viewBox="0 0 1440 720" preserveAspectRatio="xMidYMid slice" className={className} aria-hidden>
      <g fill="none" stroke="var(--trait)" strokeWidth="2" strokeLinecap="round">
        <path pathLength={1} className="trait" style={s(0.2, 2.6)} d="M-20,560 C180,470 320,640 520,560 S860,420 1060,520 S1340,620 1460,540" />
        <path pathLength={1} className="trait" style={s(0.6, 2.6)} d="M-20,620 C200,560 360,700 560,620 S900,500 1100,590 S1360,680 1460,610" />
        <path pathLength={1} className="trait" style={s(0.4, 1.4)} d="M1180,90 l14,30 l32,4 l-24,22 l7,32 l-29,-16 l-29,16 l7,-32 l-24,-22 l32,-4 Z" />
        <path pathLength={1} className="trait" style={s(1.0, 1.2)} d="M90,120 l9,19 l20,3 l-15,14 l4,20 l-18,-10 l-18,10 l4,-20 l-15,-14 l20,-3 Z" />
        <path pathLength={1} className="trait" style={s(0.8, 1.8)} d="M1300,300 q30,-40 60,0 t60,0 M1270,340 q30,-40 60,0 t60,0" />
        <path pathLength={1} className="trait" style={s(1.2, 1.6)} d="M40,330 c40,-60 100,-60 120,0 c20,60 -60,80 -80,30" />
      </g>
    </svg>
  );
}

/** Petites icônes à l'encre des trois étapes ; elles se tracent quand la carte arrive à l'écran. */
export function IconeEtape({ n }: { n: 1 | 2 | 3 }) {
  const p = { pathLength: 1, className: "trait", fill: "none", stroke: "var(--encre)", strokeWidth: 3, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  const s = (at: number) => ({ "--d": `${at}s`, "--t": "0.7s" }) as CSSProperties;
  return (
    <svg viewBox="0 0 64 64" className="size-16" aria-hidden>
      {n === 1 && <>
        <path {...p} style={s(0.1)} d="M32,8 C20,8 14,17 14,26 C14,34 20,38 22,44 H42 C44,38 50,34 50,26 C50,17 44,8 32,8 Z" />
        <path {...p} style={s(0.6)} d="M24,50 H40 M26,56 H38" />
        <path className="aplat" style={s(0.9)} d="M27,20 a7,7 0 0,1 7,-5" fill="none" stroke="var(--soleil)" strokeWidth="4" strokeLinecap="round" />
      </>}
      {n === 2 && <>
        <path {...p} style={s(0.1)} d="M20,30 a9,9 0 1,0 18,0 a9,9 0 1,0 -18,0 M8,56 C8,44 18,40 29,40 C40,40 50,44 50,56" />
        <path {...p} style={s(0.5)} d="M40,22 a7,7 0 1,0 14,0 a7,7 0 1,0 -14,0 M46,34 C54,34 60,38 60,48" />
        <circle className="aplat" style={s(0.9)} cx="47" cy="22" r="3" fill="var(--vermillon)" />
      </>}
      {n === 3 && <>
        <path {...p} style={s(0.1)} d="M10,8 H54 V56 H10 Z M10,28 H54 M32,28 V56" />
        <path className="aplat" style={s(0.8)} d="M12,30 H30 V54 H12 Z" fill="url(#trame-icone)" />
        <path {...p} style={s(0.5)} d="M16,16 q10,-8 20,0 q-4,6 -10,6 l-6,4 l1,-5 q-5,-1 -5,-5" strokeWidth={2.5} />
        <defs><pattern id="trame-icone" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="1" fill="var(--encre)" /></pattern></defs>
      </>}
    </svg>
  );
}
