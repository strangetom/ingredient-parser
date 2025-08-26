import type { Icon, IconProps } from "@tabler/icons-react";

const linkIdentifiers = ["parser", "labeller", "train"] as const;

export type LinkIdentifier = (typeof linkIdentifiers)[number];

export type Tab = {
	id: LinkIdentifier;
	component: React.ReactNode;
};

export interface Link {
	link: string;
	label: string;
	id: LinkIdentifier;
	icon: React.ForwardRefExoticComponent<IconProps & React.RefAttributes<Icon>>;
	loading?: boolean;
	disabled: boolean;
}
