import { writable, derived, type Writable, type Readable } from 'svelte/store';
import { GetSelectorsStore } from "$houdini";

// Existing stores
export const selectors = new GetSelectorsStore();
export const activeSelectors: Writable<{ [selector_id: string]: boolean }> = writable({});
export const selectedAnchor: Writable<string | null> = writable("");
export interface itemViewing {
    type: string,
    link: string,
    name: string,
    imageName: string
}
export const currentViewedItem: Writable<itemViewing | null> = writable(null);
export const errorStore = writable<string | null>(null);

selectors.subscribe(({ data }) => {
    activeSelectors.update((current) => {
        const updatedChecked = { ...current };

        if (data) {
            const selectorIds = data.selectors.map(({ id }) => id);

            selectorIds.forEach((id) => {
                if (!(id in updatedChecked)) {
                    updatedChecked[id] = false;
                }
            });

            Object.keys(updatedChecked).forEach((id) => {
                if (!selectorIds.includes(id)) {
                    delete updatedChecked[id];
                }
            });
        }

        return updatedChecked;
    });
});

// New stores
export interface File {
    name: string;
    pdfLink: string;
    imageLink: string;
    imageName: string;
}

export const files: Writable<File[]> = writable([]);

export const dynamicColumns: Readable<string[]> = derived(
    [activeSelectors, selectors],
    ([$activeSelectors, $selectors]) => {
        const columnSet: Set<string> = new Set();
        $selectors.data?.selectors.forEach((selector) => {
            if ($activeSelectors[selector.id]) {
                selector.anchors.forEach((anchor) => {
                    if (anchor.column && anchor.column !== "") {
                        columnSet.add(anchor.column);
                    }
                });
            }
        });
        return Array.from(columnSet);
    }
);
