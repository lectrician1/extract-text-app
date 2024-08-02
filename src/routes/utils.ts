import type { GetSelectors$result } from "$houdini";
import { get } from "svelte/store";
import { selectors } from "./stores";


export type JsonData = {
    analyzeResult: {
        readResults: {
            width: number;
            height: number;
            lines: { boundingBox: number[]; text: string }[];
        }[];
    };
};

export type Anchor = GetSelectors$result["selectors"][0]["anchors"][0]


export function getAnchorData(anchorId: string): Anchor | undefined {
    let selectorsNow = get(selectors);
    if (!selectorsNow.data) return undefined;
    const anchor = selectorsNow.data.selectors
        .flatMap((selector: { anchors: GetSelectors$result["selectors"][0]["anchors"] }) => selector.anchors)
        .find((anchor: Anchor) => anchor.id === anchorId);
    return anchor;
}



export async function loadJsonData(imageName: string): Promise<JsonData> {
    try {
        const opfsRoot = await navigator.storage.getDirectory();
        const jsonDirHandle = await opfsRoot
            .getDirectoryHandle("json", { create: false })
            .catch(() => null);
        if (jsonDirHandle) {
            const jsonHandle = await jsonDirHandle
                .getFileHandle(`${imageName}.json`, { create: false })
                .catch(() => null);
            if (jsonHandle) {
                const file = await jsonHandle.getFile();
                const text = await file.text();
                return JSON.parse(text);
            }
            throw new Error("File not found");
        }
        throw new Error("json directory not found");
    } catch (err) {
        throw new Error("Error loading JSON data:" + err);
    }
}

export function boxCenterIsInCircle(boxCenterX: number, boxCenterY: number, circleX: number, circleY: number, circleRadius: number): boolean {
    const distance = Math.sqrt(
        Math.pow(boxCenterX - circleX!, 2) +
        Math.pow(boxCenterY - circleY!, 2),
    );
    return distance <= circleRadius!
}