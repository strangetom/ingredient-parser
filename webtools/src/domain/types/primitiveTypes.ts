export type Json = string | number | boolean | null | JsonArray | JsonObject;

interface JsonObject {
	[key: string]: Json;
}

interface JsonArray extends Array<Json> {}
