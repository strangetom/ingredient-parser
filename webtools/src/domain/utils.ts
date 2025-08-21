/* Dates */

export const formattedCountdownSeconds = (seconds: number) => {
	const dt = new Date(0);
	dt.setSeconds(seconds);
	return dt.toISOString().substring(15, 19);
};

export const formattedCounterSeconds = (seconds: number) => {
	const hh = String(Math.floor(seconds / 3600)).padStart(2, "0");
	const mm = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
	const ss = String(seconds % 60).padStart(2, "0");

	return `${hh}:${mm}:${ss}`;
};

export function getTodayByMonthFullStr(): string {
	return new Date().toLocaleString("en-US", { month: "short" });
}

export function getTodayByDayFullStr(): string {
	return new Date().toLocaleString("en-US", { day: "numeric" });
}

export function getTodayByMonth(): number {
	return new Date().getDate();
}

export function getTodayByFull365(): number {
	return Math.floor(
		(Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) /
			1000 /
			60 /
			60 /
			24,
	);
}

export function isValidDayOf365(day: string): boolean {
	return parseInt(day, 10) >= 1 && parseInt(day, 10) <= 365;
}

export function setTimer(finaleDate: Date): Record<string, number> {
	const now = Date.now();
	const diff = finaleDate.getTime() - now;

	const days = Math.floor(diff / (1000 * 60 * 60 * 24));
	const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
	const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
	const seconds = Math.floor((diff % (1000 * 60)) / 1000);

	return {
		days: days,
		hours: hours,
		minutes: minutes,
		seconds: seconds,
	};
}

export function updateCountdown(): string {
	const now = new Date();
	const tomorrow = new Date();
	tomorrow.setHours(24, 0, 0, 0); // Set to midnight tomorrow

	const timeRemaining = tomorrow.getTime() - now.getTime();

	const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
	const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
	const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);

	return `${hours}h ${minutes}m ${seconds}s`;
}

/* Strings */

export function getInitials(name: string, limit = 2) {
	const splitted = name.split(" ");

	if (splitted.length === 1) {
		return name.slice(0, 1).toUpperCase();
	}

	return splitted
		.map((word) => word[0])
		.slice(0, limit)
		.join("")
		.toUpperCase();
}

export function splitName(name: string, option: "first" | "last"): string {
	if (option === "first") return name.split(" ").slice(0, -1).join(" ");
	else if (option === "last") return name.split(" ").slice(-1).join(" ");
	else return name;
}

export function toTitleCase(str: string) {
	return str.replace(
		/\w\S*/g,
		(txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase(),
	);
}

export function isAlphaLetter(str: string) {
	return str.toUpperCase() !== str.toLowerCase();
}

// https://stackoverflow.com/questions/36637146/encode-string-to-hex
export function hex(str: string) {
	return str
		.split("")
		.map((c) => c.charCodeAt(0).toString(16).padStart(2, "0"))
		.join("");
}

export function dehex(str: string) {
	return str
		.split(/(\w\w)/g)
		.filter((p) => !!p)
		.map((c) => String.fromCharCode(parseInt(c, 16)))
		.join("");
}

/* Numbers */

export function getRandomArbitrary(min: number, max: number): number {
	return Math.floor(Math.random() * (max - min) + min);
}

export function getRandomArbitraryFloat(min: number, max: number): number {
	return Math.random() * (max - min) + min;
}

export function getRandomArbitraryAndExclude(
	min: number,
	max: number,
	exclude: number[],
) {
	let n = Math.floor(Math.random() * (max - min) + min);
	exclude.every((num) => {
		if (n >= num) {
			n++;
			return false;
		}
		return true;
	});
	return n;
}

export function ordinal(integer: number): string {
	const s = ["th", "st", "nd", "rd"];
	const v = integer % 100;
	return integer + (s[(v - 20) % 10] || s[v] || s[0]);
}

export function romanize(integer: number): string {
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
		I: 1,
	} as Record<string, number>;
	let roman = "";
	let i: string;
	for (i in lookup) {
		while (integer >= lookup[i]) {
			roman += i;
			integer -= lookup[i];
		}
	}
	return roman;
}

/* Primitives */

export function validateJson(
	value: string | null | undefined,
	deserialize: typeof JSON.parse,
) {
	if (typeof value === "string" && value.trim().length === 0) {
		return true;
	}

	if (!value) {
		return false;
	}

	try {
		deserialize(value);
		return true;
	} catch (_) {
		return false;
	}
}

export function safeParseJsonPrettyStringify(
	value: string | null | undefined,
	deserialize: typeof JSON.parse,
	serialize: typeof JSON.stringify,
) {
	const fallback = "{}";

	if ((typeof value === "string" && value.trim().length === 0) || !value) {
		return serialize(JSON.parse(fallback), null, 2);
	}

	try {
		deserialize(value);
		return serialize(JSON.parse(value), null, 2);
	} catch (_) {
		return serialize(JSON.parse(fallback), null, 2);
	}
}

export function intersection<T>(a: Array<T>, b: Array<T>): Array<T> {
	return a.filter((o) => b.includes(o));
}

export function difference<T>(a: Array<T>, b: Array<T>): Array<T> {
	return a.filter((o) => !b.includes(o));
}

export function union<T>(a: Array<T>, b: Array<T>): Array<T> {
	return [...new Set([...a, ...b])];
}

export function shuffle<T>(
	// https://bost.ocks.org/mike/shuffle/
	list: Array<T>,
): Array<T> {
	let m = list.length,
		t: T,
		i: number;

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
	if (hostname.startsWith("www.")) {
		hostname = hostname.substring(4); // Remove 'www.'
	}
	return hostname;
}

export function utmParameterize(url: string) {
	const source = "utm_source=ingredientparser";
	const medium = "utm_medium=referral";
	const name = "utm_campaign=ingredientparser";
	return `${url}?${[source, medium, name].join("&")}`;
}

/* Colors */

export function hexToRgb(hex: string) {
	const hexstr = hex.slice(1);
	const bigint = parseInt(hexstr, 16);
	const r = (bigint >> 16) & 255;
	const g = (bigint >> 8) & 255;
	const b = bigint & 255;

	return `rgb(${[r, g, b].join(",")})`;
}
