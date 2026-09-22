import AllRecipes from "../../assets/publishers/logo.allrecipes.svg";
import TheBBC from "../../assets/publishers/logo.bbc.svg";
import BonAppetit from "../../assets/publishers/logo.bonappetite.svg";
import CookStr from "../../assets/publishers/logo.cookstr.svg";
import TheNYTCooking from "../../assets/publishers/logo.nytcooking.svg";
import Taste from "../../assets/publishers/logo.taste.svg";

export interface CollectionPublisherSource {
	abbr: string;
	name: string;
	logo: string | null;
}

export const collectionPublisherSources: CollectionPublisherSource[] = [
	{
		abbr: "nyt",
		name: "New York Times Cooking",
		logo: TheNYTCooking,
	},
	{
		abbr: "ba",
		name: "BonAppetit",
		logo: BonAppetit,
	},
	{
		abbr: "bbc",
		name: "BBC",
		logo: TheBBC,
	},
	{
		abbr: "allrecipes",
		name: "AllRecipes",
		logo: AllRecipes,
	},
	{
		abbr: "tc",
		name: "Taste Cooking",
		logo: Taste,
	},
	{
		abbr: "cookstr",
		name: "CookStr",
		logo: CookStr,
	},
];

export default collectionPublisherSources;
