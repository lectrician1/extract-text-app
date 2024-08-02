<script lang="ts">
    import Container from "./Container.svelte";
    import {
        currentViewedItem,
        selectedAnchor,
        selectors,
        type itemViewing,
    } from "./stores.ts";
    import { afterUpdate } from "svelte";
    import { UpdateAnchorStore } from "$houdini";
    import { get } from "svelte/store";
    import {
        boxCenterIsInCircle,
        loadJsonData,
        getAnchorData,
        type JsonData,
    } from "./utils.ts";

    let item: itemViewing | null;
    let canvasElement: HTMLCanvasElement | null = null;
    let ctx: CanvasRenderingContext2D | null = null;
    let jsonData: JsonData | null = null;
    let imageElement: HTMLImageElement | null = null;

    // Variables for zoom and pan
    let scale = 1;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let startX = 0;
    let startY = 0;

    // Variable to store the selected bounding box
    let selectedBox: { boundingBox: number[]; text: string } | null = null;

    $: item = $currentViewedItem;

    function loadAndDrawImage(): void {
        imageElement = new Image();
        imageElement.onload = () => {
            const canvasHeight = 800;
            const canvasWidth = 600;

            canvasElement!.width = canvasWidth;
            canvasElement!.height = canvasHeight;

            drawImageWithBoundingBoxes();
        };
        imageElement.src = item!.link;
    }

    function drawImageWithBoundingBoxes(): void {
        if (!jsonData || !ctx || !imageElement) return;

        ctx.clearRect(0, 0, canvasElement!.width, canvasElement!.height);
        ctx.save();
        ctx.translate(panX, panY);
        ctx.scale(scale, scale);

        ctx.drawImage(
            imageElement,
            0,
            0,
            imageElement.width,
            imageElement.height,
        );

        const {
            width: originalWidth,
            height: originalHeight,
            lines,
        } = jsonData.analyzeResult.readResults[0];
        const scaleX = imageElement.width / originalWidth;
        const scaleY = imageElement.height / originalHeight;

        let selectedAnchorNow = get(selectedAnchor);
        let selectedAnchorData = selectedAnchorNow
            ? getAnchorData(selectedAnchorNow)
            : undefined;
        let centerX: number | undefined, centerY: number | undefined;
        let circleX: number | undefined,
            circleY: number | undefined,
            circleRadius: number | undefined;

        if (selectedBox && selectedAnchorData) {
            const [x1, y1, , , x2, y2] = selectedBox.boundingBox;
            centerX = (x1 * scaleX + x2 * scaleX) / 2;
            centerY = (y1 * scaleY + y2 * scaleY) / 2;

            if (
                selectedAnchorData.dist_right &&
                selectedAnchorData.dist_down &&
                selectedAnchorData.radius
            ) {
                circleX = centerX + selectedAnchorData.dist_right;
                circleY = centerY + selectedAnchorData.dist_down;
                circleRadius = selectedAnchorData.radius;

                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.lineTo(circleX, circleY);
                ctx.strokeStyle = "blue";
                ctx.lineWidth = 2 / scale;
                ctx.stroke();

                ctx.beginPath();
                ctx.arc(circleX, circleY, circleRadius, 0, 2 * Math.PI);
                ctx.strokeStyle = "green";
                ctx.lineWidth = 2 / scale;
                ctx.stroke();
            }
        }

        for (const line of lines) {
            const bbox = line.boundingBox;
            const [x1, y1, x2, y2, x3, y3, x4, y4] = bbox;
            const boxCenterX = (x1 * scaleX + x3 * scaleX) / 2;
            const boxCenterY = (y1 * scaleY + y3 * scaleY) / 2;

            ctx.beginPath();
            ctx.moveTo(x1 * scaleX, y1 * scaleY);
            ctx.lineTo(x2 * scaleX, y2 * scaleY);
            ctx.lineTo(x3 * scaleX, y3 * scaleY);
            ctx.lineTo(x4 * scaleX, y4 * scaleY);
            ctx.closePath();

            if (
                selectedAnchorData &&
                circleX &&
                circleY &&
                circleRadius &&
                boxCenterIsInCircle(
                    boxCenterX,
                    boxCenterY,
                    circleX,
                    circleY,
                    circleRadius,
                )
            ) {
                ctx.fillStyle = "rgba(255, 165, 0, 0.2)";
                ctx.fill();
            }

            if (line === selectedBox) {
                ctx.fillStyle = "rgba(0, 255, 0, 0.2)";
                ctx.fill();
            }

            ctx.strokeStyle = "red";
            ctx.lineWidth = 2 / scale;
            ctx.stroke();
        }

        ctx.restore();
    }

    function handleWheel(event: WheelEvent): void {
        event.preventDefault();
        const zoomIntensity = 0.1;
        const rect = canvasElement!.getBoundingClientRect();
        const offsetX = event.clientX - rect.left;
        const offsetY = event.clientY - rect.top;
        const wheel = event.deltaY < 0 ? 1 : -1;
        const zoom = Math.exp(wheel * zoomIntensity);

        const newScale = scale * zoom;
        panX = offsetX - (offsetX - panX) * zoom;
        panY = offsetY - (offsetY - panY) * zoom;
        scale = newScale;

        drawImageWithBoundingBoxes();
    }

    async function handleMouseDown(event: MouseEvent): Promise<void> {
        if ($selectedAnchor) {
            const rect = canvasElement!.getBoundingClientRect();
            const mouseX = (event.clientX - rect.left - panX) / scale;
            const mouseY = (event.clientY - rect.top - panY) / scale;

            const lines = jsonData!.analyzeResult.readResults[0].lines;
            const originalWidth = jsonData!.analyzeResult.readResults[0].width;
            const originalHeight =
                jsonData!.analyzeResult.readResults[0].height;
            const scaleX = imageElement!.width / originalWidth;
            const scaleY = imageElement!.height / originalHeight;

            let clickedBox: { boundingBox: number[]; text: string } | null =
                null;
            for (const line of lines) {
                const bbox = line.boundingBox;
                const scaledBbox = [
                    bbox[0] * scaleX,
                    bbox[1] * scaleY,
                    bbox[2] * scaleX,
                    bbox[3] * scaleY,
                    bbox[4] * scaleX,
                    bbox[5] * scaleY,
                    bbox[6] * scaleX,
                    bbox[7] * scaleY,
                ];

                if (isPointInPolygon(mouseX, mouseY, scaledBbox)) {
                    clickedBox = line;
                    break;
                }
            }

            if (clickedBox) {
                if (clickedBox !== selectedBox) {
                    selectedBox = clickedBox;
                    drawImageWithBoundingBoxes();

                    // If an anchor is selected, update its text with the clicked box's text
                    const updateAnchorStore = new UpdateAnchorStore();
                    try {
                        await updateAnchorStore.mutate({
                            id: $selectedAnchor,
                            _set: { anchor_text: clickedBox.text },
                        });
                        console.log("Anchor text updated successfully");
                    } catch (error) {
                        console.error("Error updating anchor text:", error);
                    }
                }
            } else {
                isPanning = true;
                startX = event.clientX - panX;
                startY = event.clientY - panY;
            }
        } else {
            isPanning = true;
            startX = event.clientX - panX;
            startY = event.clientY - panY;
        }
    }

    function isPointInPolygon(
        x: number,
        y: number,
        polygon: number[],
    ): boolean {
        let inside = false;
        for (
            let i = 0, j = polygon.length - 2;
            i < polygon.length;
            j = i, i += 2
        ) {
            const xi = polygon[i],
                yi = polygon[i + 1];
            const xj = polygon[j],
                yj = polygon[j + 1];

            const intersect =
                yi > y !== yj > y &&
                x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
            if (intersect) inside = !inside;
        }
        return inside;
    }

    function handleMouseMove(event: MouseEvent): void {
        if (!isPanning) return;
        panX = event.clientX - startX;
        panY = event.clientY - startY;
        drawImageWithBoundingBoxes();
    }

    function handleMouseUp(): void {
        isPanning = false;
    }

    async function refindAndCenterText(): Promise<void> {
        const anchorId = get(selectedAnchor);
        if (anchorId) {
            const anchor = getAnchorData(anchorId);
            if (anchor) {
                // Find the first occurrence of the anchor text
                const lines = jsonData!.analyzeResult.readResults[0].lines;
                selectedBox =
                    lines.find(
                        (line) =>
                            anchor.anchor_text &&
                            line.text.includes(anchor.anchor_text),
                    ) || null;

                if (selectedBox) {
                    const selectedBbox = selectedBox.boundingBox;
                    const originalWidth =
                        jsonData!.analyzeResult.readResults[0].width;
                    const originalHeight =
                        jsonData!.analyzeResult.readResults[0].height;
                    const scaleX = imageElement!.width / originalWidth;
                    const scaleY = imageElement!.height / originalHeight;

                    const centerX =
                        ((selectedBbox[0] + selectedBbox[4]) / 2) * scaleX;
                    const centerY =
                        ((selectedBbox[1] + selectedBbox[5]) / 2) * scaleY;

                    if (
                        anchor.dist_right !== null &&
                        anchor.dist_down !== null
                    ) {
                        // Center on the circle if dist_right and dist_down are not null
                        const circleX = centerX + anchor.dist_right;
                        const circleY = centerY + anchor.dist_down;

                        panX = canvasElement!.width / 2 - circleX * scale;
                        panY = canvasElement!.height / 2 - circleY * scale;
                    } else {
                        // Center on the selected bbox if dist_right or dist_down is null
                        panX = canvasElement!.width / 2 - centerX * scale;
                        panY = canvasElement!.height / 2 - centerY * scale;
                    }
                }

                drawImageWithBoundingBoxes();
            }
        }
    }

    selectedAnchor.subscribe(async () => {
        await refindAndCenterText();
    });

    selectors.subscribe(() => {
        if (get(selectedAnchor)) {
            refindAndCenterText();
        } else {
            drawImageWithBoundingBoxes();
        }
    });

    afterUpdate(async () => {
        if (item && item.type === "imageLink") {
            canvasElement = document.getElementById(
                "bounding-box-canvas",
            ) as HTMLCanvasElement;
            ctx = canvasElement.getContext("2d");
            jsonData = await loadJsonData(item.imageName);
            loadAndDrawImage();
        }
    });
</script>

<Container header="Viewer">
    {#if item}
        {#if item.type === "pdfLink"}
            <iframe
                src={item.link}
                title={item.name}
                width="100%"
                height="600px"
            ></iframe>
        {:else if item.type === "imageLink"}
            <div style="position: relative; display: inline-block;">
                <canvas
                    id="bounding-box-canvas"
                    style="border: 1px solid black;"
                    on:wheel={handleWheel}
                    on:mousedown={handleMouseDown}
                    on:mousemove={handleMouseMove}
                    on:mouseup={handleMouseUp}
                    on:mouseleave={handleMouseUp}
                ></canvas>
            </div>
        {/if}
    {:else}
        <p>No item selected</p>
    {/if}
</Container>

<style>
    #bounding-box-canvas {
        max-width: 100%;
        max-height: 800px;
    }
</style>
