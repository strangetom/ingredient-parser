import AllRecipes from "../../../assets/publishers/logo.allrecipes.svg";
import TheBBC from "../../../assets/publishers/logo.bbc.svg";
import CookStr from "../../../assets/publishers/logo.cookstr.svg";
import TheNYTCooking from "../../../assets/publishers/logo.nytcooking.svg";
//import Saveur from "../../../assets/publishers/logo.saveur.svg";
import Taste from "../../../assets/publishers/logo.taste.svg";

interface Source {
	abbr: string;
	name: string;
	logo: string;
}

export const sources: Source[] = [
	{
		abbr: "nyt",
		name: "New York Times Cooking",
		logo: TheNYTCooking,
	},
	/*
  {
    abbr: "saveur",
    name: "Saveur",
    logo: Saveur,
  },
   */
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
