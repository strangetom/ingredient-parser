
/* Dates */

export const formattedCountdownSeconds = (seconds: number) => {
  const dt = (new Date(0))
  dt.setSeconds(seconds)
  return dt.toISOString().substring(15, 19)
}

export const formattedCounterSeconds = (seconds: number) => {
  const hh = String(Math.floor(seconds / 3600)).padStart(2, '0');
  const mm = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
  const ss = String(seconds % 60).padStart(2, '0');

  return `${hh}:${mm}:${ss}`;
}

export function getTodayByMonthFullStr(): string {
  return new Date().toLocaleString('en-US', { month: 'short' });
}

export function getTodayByDayFullStr(): string {
  return new Date().toLocaleString('en-US', { day: 'numeric' });
}

export function getTodayByMonth(): number {
  return new Date().getDate()
}

export function getTodayByFull365(): number {
  return Math.floor(
    (new Date().getTime() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 1000 / 60 / 60 / 24
  )
}

export function isValidDayOf365(
  day: string
): boolean {
  return parseInt(day) >= 1 && parseInt(day) <= 365
}

export function setTimer(
  finaleDate: Date
): Record<string, number> {

  const now = new Date().getTime();
  const diff = finaleDate.getTime() - now;

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor(diff % (1000 * 60 * 60 * 24) / (1000 * 60 * 60));
  const minutes = Math.floor(diff % (1000 * 60 * 60) / (1000 * 60));
  const seconds = Math.floor(diff % (1000 * 60) / 1000);

  return {
    days: days,
    hours: hours,
    minutes: minutes,
    seconds: seconds
  }

}

export function updateCountdown(): string {

    const now = new Date() as Date;
    const tomorrow = new Date() as Date;
    tomorrow.setHours(24, 0, 0, 0); // Set to midnight tomorrow

    const timeRemaining = (tomorrow as any) - (now as any);

    const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
    const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);

    return `${hours}h ${minutes}m ${seconds}s`;

}

/* Strings */

export function getInitials(name: string, limit = 2) {
  const splitted = name.split(' ');

  if (splitted.length === 1) {
    return name.slice(0, 1).toUpperCase();
  }

  return splitted
    .map((word) => word[0])
    .slice(0, limit)
    .join('')
    .toUpperCase();
}

export function splitName(
  name: string,
  option: "first" | "last"
): string {
  if (option === "first") return name.split(' ').slice(0, -1).join(' ');
  else if (option === "last") return name.split(' ').slice(-1).join(' ');
  else return name
}

export function toTitleCase(
  str: string
) {
  return str.replace(
    /\w\S*/g,
    function(txt) {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    }
  );
}

export function isAlphaLetter(
  str: string
) {
  return str.toUpperCase() !== str.toLowerCase()
}

// https://stackoverflow.com/questions/14458819/simplest-way-to-obfuscate-and-deobfuscate-a-string-in-javascript
export function obfs(
  str: string,
  key: number,
  n = 126
): string {
  // return String itself if the given parameters are invalid
  if (!(typeof (key) === 'number' && key % 1 === 0)
    || !(typeof (key) === 'number' && key % 1 === 0)) {
    return str.toString();
  }

  const chars = str.toString().split('');

  for (let i = 0; i < chars.length; i++) {
    const c = chars[i].charCodeAt(0);

    if (c <= n) {
      chars[i] = String.fromCharCode((chars[i].charCodeAt(0) + key) % n);
    }
  }

  return chars.join('');
};

// https://stackoverflow.com/questions/14458819/simplest-way-to-obfuscate-and-deobfuscate-a-string-in-javascript
export function deobf(
  str: string,
  key: number,
  n = 126
): string {
  // return String itself if the given parameters are invalid
  if (!(typeof (key) === 'number' && key % 1 === 0)
    || !(typeof (key) === 'number' && key % 1 === 0)) {
    return str.toString();
  }

  return obfs(str.toString(), n - key);
};

// https://stackoverflow.com/questions/36637146/encode-string-to-hex
export function hex(
  str: string
) {
  return str.split("").map(c => c.charCodeAt(0).toString(16).padStart(2, "0")).join("");
}

export function dehex(
  str: string
) {
  return str.split(/(\w\w)/g).filter(p => !!p).map(c => String.fromCharCode(parseInt(c, 16))).join("")
}

/* Numbers */

export function getRandomArbitrary(
  min: number,
  max: number
): number {
  return Math.floor(Math.random() * (max - min) + min)
}

export function getRandomArbitraryFloat(
  min: number,
  max: number
): number {
  return Math.random() * (max - min) + min
}

export function getRandomArbitraryAndExclude(
  min: number,
  max: number,
  exclude: number[]
) {
  let n = Math.floor(Math.random() * (max - min) + min)
  exclude.every(num => {
    if (n >= num) {
      n++;
      return false;
    }
    return true
  })
  return n;
}

export function ordinal(
  integer: number
): string {
  const s = ["th", "st", "nd", "rd"];
  const v = integer % 100;
  return integer + (s[(v - 20) % 10] || s[v] || s[0]);
}

export function romanize(
  integer: number
): string {
  const lookup = {
    M: 1000,
    CM: 900,
    D: 500,
    CD: 400,
    C: 100,
    XC: 90,
    L: 50,
    XL: 40,
    X: 10,
    IX: 9,
    V: 5,
    IV: 4,
    I: 1
  } as Record<string, number>;
  let roman = '';
  let i;
  for (i in lookup) {
    while (integer >= lookup[i]) {
      roman += i;
      integer -= lookup[i];
    }
  }
  return roman;
}

/* Primitives */

export function intersection(
  a: Array<string | number | null | undefined>,
  b: Array<string | number | null | undefined>
): Array<string | number | null | undefined> {
  return a.filter(o => b.includes(o));
}

export function difference(
  a: Array<string | number | null | undefined>,
  b: Array<string | number | null | undefined>
): Array<string | number | null | undefined> {
  return a.filter(o => !b.includes(o));
}

export function union(
  a: Array<string | number | null | undefined>,
  b: Array<string | number | null | undefined>
): Array<string | number | null | undefined> {
  return [...new Set([...a, ...b])];
}

export function shuffle( // https://bost.ocks.org/mike/shuffle/
  list: Array<any>
): Array<any> {
  let m = list.length, t, i;

  while (m) {

    i = Math.floor(Math.random() * m--);

    t = list[m];
    list[m] = list[i];
    list[i] = t;
  }

  return list;
}

/* URLs */

export function getHostFromUrl(url: string) {
    const parsedUrl = new URL(url);
    let hostname = parsedUrl.hostname;
    if (hostname.startsWith('www.')) {
        hostname = hostname.substring(4); // Remove 'www.'
    }
    return hostname;
}

export function utmParameterize(url: string) {
  const source = 'utm_source=theblankdish'
  const medium = 'utm_medium=referral'
  const name = 'utm_campaign=theblankdish'
  return url + `?${[source, medium, name].join('&')}`
}

/* Colors */

export function hexToRgb(hex: string) {
    const hexstr = hex.slice(1)
    const bigint = parseInt(hexstr, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;

    return "rgb(" + [r, g, b].join(',') + ")"
}

interface HSL {
  h:number,
  s:number,
  l:number
}

export function hslFromRgb(rgb: string): HSL {

  const rgbArr = rgb.replace(/[^0-9,]/g,'').split(",")
  const r1 = Number(rgbArr[0]) / 255,
        g1 = Number(rgbArr[1]) / 255,
        b1 = Number(rgbArr[2]) / 255;

  const maxColor = Math.max(r1,g1,b1),
        minColor = Math.min(r1,g1,b1);

  let L = (maxColor + minColor) / 2 ,
      S = 0,
      H = 0;

  if(maxColor != minColor){
    if(L < 0.5){
      S = (maxColor - minColor) / (maxColor + minColor);
    }else{
      S = (maxColor - minColor) / (2.0 - maxColor - minColor);
    }
    if(r1 == maxColor){
      H = (g1-b1) / (maxColor - minColor);
    }else if(g1 == maxColor){
      H = 2.0 + (b1 - r1) / (maxColor - minColor);
    }else{
      H = 4.0 + (r1 - g1) / (maxColor - minColor);
    }
  }
  L = L * 100;
  S = S * 100;
  H = H * 60;
  if(H<0){
    H += 360;
  }
  return {h:H, s:S, l:L};
}

export function colorNameFromHsl(hsl: HSL): string {

    const l = Math.floor(hsl.l),
          s = Math.floor(hsl.s),
          h = Math.floor(hsl.h);

    if (s <= 10 && l >= 90) {
        return ("white")
    } else if (l <= 15) {
        return ("black")
    } else if ((s <= 10 && l <= 70) || s === 0) {
        return ("gray")
    } else if ((h >= 0 && h <= 15) || h >= 346) {
        return ("red");
    } else if (h >= 16 && h <= 35) {
        if (s < 90) {
            return ("brown");
        } else {
            return ("orange");
        }
    } else if (h >= 36 && h <= 54) {
        if (s < 90) {
            return ("brown");
        } else {
            return ("yellow");
        }
    } else if (h >= 55 && h <= 165) {
        return ("green");
    } else if (h >= 166 && h <= 260) {
        return ("blue")
    } else if (h >= 261 && h <= 290) {
        return ("purple")
    } else if (h >= 291 && h <= 345) {
        return ("pink")
    }
    else {
      return ("white")
    }
}
