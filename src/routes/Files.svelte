<script lang="ts">
    import { TabulatorFull as Tabulator } from "tabulator-tables";
    import { onMount, tick, onDestroy } from "svelte";
    import Container from "./Container.svelte";
    import { Button, Spinner, Modal } from "flowbite-svelte";
    import { get, derived } from "svelte/store";
    import {
        currentViewedItem,
        selectors,
        dynamicColumns,
        activeSelectors,
        files,
        type File,
    } from "./stores";
    import { loadJsonData, getAnchorData, boxCenterIsInCircle } from "./utils";
    const baseUrl = import.meta.env.VITE_BASE_URL;

    let tableComponent: string | HTMLElement;
    let table: Tabulator;
    let intervalId: string | number | NodeJS.Timeout | undefined;
    let processingFiles = false;
    let showModal = false;
    let processedCount = 0;
    let totalCount = 0;

    function areAllNamesPresent(myFiles, newFiles) {
        if (myFiles.length === 0 || newFiles.length === 0) return false;

        const myFileNames = new Set(myFiles.map((file) => file.name));
        const newFileNames = new Set(newFiles.map((file) => file.name));

        const allMyFilesInNewFiles = myFiles.every((file) =>
            newFileNames.has(file.name),
        );
        const allNewFilesInMyFiles = newFiles.every((file) =>
            myFileNames.has(file.name),
        );

        return allMyFilesInNewFiles && allNewFilesInMyFiles;
    }

    async function getFilesFromOPFS() {
        let newFiles: File[] = [];
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            const imageDirHandle = await opfsRoot
                .getDirectoryHandle("images", { create: false })
                .catch(() => null);
            if (imageDirHandle) {
                for await (const [
                    imageName,
                    handle,
                ] of imageDirHandle.entries()) {
                    if (
                        handle.kind === "file" &&
                        (imageName.endsWith(".png") ||
                            imageName.endsWith(".jpg"))
                    ) {
                        const jsonFileName = `${imageName}.json`;
                        const jsonFileExists = await fileExists(
                            jsonFileName,
                            "json",
                        );

                        if (jsonFileExists) {
                            const link = await handle
                                .getFile()
                                .then((file) => URL.createObjectURL(file));
                            const pdfName = imageName.split("_")[0] + ".pdf";
                            const pdfLink = await findPDFLink(
                                pdfName,
                                opfsRoot,
                            );

                            const originalFileName = pdfLink
                                ? pdfName
                                : imageName;

                            newFiles.push({
                                name: originalFileName,
                                pdfLink: pdfLink || "",
                                imageLink: link,
                                imageName: imageName,
                            });
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Error getting files from OPFS:", err);
        }

        if (!areAllNamesPresent(get(files), newFiles)) {
            files.set(newFiles);
        }
    }

    async function findPDFLink(
        pdfName: string,
        opfsRoot: FileSystemDirectoryHandle,
    ) {
        try {
            const pdfDirHandle = await opfsRoot
                .getDirectoryHandle("pdf", { create: false })
                .catch(() => null);
            if (pdfDirHandle) {
                for await (const [name, handle] of pdfDirHandle.entries()) {
                    if (handle.kind === "file" && name === pdfName) {
                        return handle
                            .getFile()
                            .then((file) => URL.createObjectURL(file));
                    }
                }
            }
        } catch (err) {
            console.error("Error finding PDF link:", err);
        }
        return null;
    }

    async function fileExists(fileName: string, directoryName: string) {
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            const dirHandle = await opfsRoot.getDirectoryHandle(directoryName, {
                create: false,
            });
            await dirHandle.getFileHandle(fileName, { create: false });
            return true;
        } catch (err) {
            return false;
        }
    }

    async function deleteFile(fileName: string, directoryName: string) {
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            const dirHandle = await opfsRoot.getDirectoryHandle(directoryName, {
                create: false,
            });
            await dirHandle.removeEntry(fileName);
        } catch (err) {
            console.error(
                `Error deleting file ${fileName} from ${directoryName}:`,
                err,
            );
        }
    }

    async function handleDelete(row) {
        const imageName = row.getData().imageName;
        await deleteFile(imageName, "images");
        await deleteFile(`${imageName}.json`, "json");

        const opfsRoot = await navigator.storage.getDirectory();
        const imageDirHandle = await opfsRoot
            .getDirectoryHandle("images", { create: false })
            .catch(() => null);
        let pdfShouldBeDeleted = true;
        if (imageDirHandle) {
            for await (const [name, handle] of imageDirHandle.entries()) {
                if (
                    name.startsWith(imageName.split("_")[0]) &&
                    name !== imageName
                ) {
                    pdfShouldBeDeleted = false;
                    break;
                }
            }
        }
        if (pdfShouldBeDeleted) {
            const pdfName = imageName.split("_")[0] + ".pdf";
            if (await fileExists(pdfName, "pdf")) {
                await deleteFile(pdfName, "pdf");
            }
        }
    }

    function handleLinkClick(e, cell) {
        e.preventDefault();
        const link = cell.getValue();
        const rowData = cell.getRow().getData();
        currentViewedItem.set({
            type: cell.getField(),
            link,
            name: rowData.name,
            imageName: rowData.imageName,
        });
    }

    function startPeriodicOPFSQuery() {
        intervalId = setInterval(getFilesFromOPFS, 500);
    }

    onMount(() => {
        const init = async () => {
            await getFilesFromOPFS();
            startPeriodicOPFSQuery();

            const unsubscribe = derived(
                [files, dynamicColumns, selectors],
                ([$files, $dynamicColumns, $selectors]) => ({
                    $files,
                    $dynamicColumns,
                    $selectors,
                }),
            ).subscribe(async ({ $files, $dynamicColumns, $selectors }) => {
                await tick();
                if (!table) {
                    const columns = [
                        { title: "Name", field: "name", width: 150 },
                        {
                            title: "PDF",
                            field: "pdfLink",
                            formatter: (cell) => {
                                const link = cell.getValue();
                                return link
                                    ? `<a href="${link}" target="_blank" class="pdf-link">PDF</a>`
                                    : "";
                            },
                            cellClick: handleLinkClick,
                        },
                        {
                            title: "Image",
                            field: "imageLink",
                            formatter: (cell) => {
                                const link = cell.getValue();
                                return link
                                    ? `<a href="${link}" target="_blank" class="image-link">Image</a>`
                                    : "";
                            },
                            cellClick: handleLinkClick,
                        },
                        {
                            title: "Actions",
                            field: "actions",
                            formatter: () =>
                                `<button class="delete-btn">🗑️</button>`,
                            cellClick: (e, cell) => handleDelete(cell.getRow()),
                        },
                        ...$dynamicColumns.map((column) => ({
                            title: column,
                            field: column,
                        })),
                    ];

                    table = new Tabulator(tableComponent, {
                        data: await enrichFileData(),
                        columns: columns,
                    });
                } else {
                    let updatedColumns = [
                        ...table
                            .getColumnDefinitions()
                            .filter((col) =>
                                [
                                    "name",
                                    "pdfLink",
                                    "imageLink",
                                    "actions",
                                ].includes(col.field),
                            ),
                        ...$dynamicColumns.map((column) => ({
                            title: column,
                            field: column,
                        })),
                    ];

                    let data = await enrichFileData();
                    table.setColumns(updatedColumns);
                    table.replaceData(data);
                }
            });

            return () => {
                unsubscribe();
                if (intervalId) {
                    clearInterval(intervalId);
                }
            };
        };

        init();
    });

    onDestroy(() => {
        if (intervalId) {
            clearInterval(intervalId);
        }
    });

    async function extractTextFromImage(imageBlob: Blob) {
        const reader = new FileReader();
        return new Promise((resolve, reject) => {
            reader.onloadend = async () => {
                const base64Image = reader.result.split(",")[1];
                const extractUrl = `${baseUrl}/api/extract-text`;
                const response = await fetch(extractUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ imageData: base64Image }),
                });

                const result = await response.json();
                resolve(result);
            };
            reader.onerror = reject;
            reader.readAsDataURL(imageBlob);
        });
    }

    async function handleFileUpload() {
        processingFiles = true;
        processedCount = 0;
        try {
            const fileHandles = await window.showOpenFilePicker({
                multiple: true,
                types: [
                    {
                        description: "Image and PDF files",
                        accept: {
                            "image/tiff": [".tiff"],
                            "image/png": [".png"],
                            "image/jpeg": [".jpeg", ".jpg"],
                            "application/pdf": [".pdf"],
                        },
                    },
                ],
            });
            totalCount = fileHandles.length;
            const opfsRoot = await navigator.storage.getDirectory();
            const imageDir = await opfsRoot.getDirectoryHandle("images", {
                create: true,
            });
            const pdfDir = await opfsRoot.getDirectoryHandle("pdf", {
                create: true,
            });
            const jsonDir = await opfsRoot.getDirectoryHandle("json", {
                create: true,
            });

            const processFile = async (fileHandle) => {
                const file = await fileHandle.getFile();
                const fileName = file.name;

                if (fileName.endsWith(".pdf")) {
                    const pdfFileHandle = await pdfDir.getFileHandle(fileName, {
                        create: true,
                    });
                    const pdfWritable = await pdfFileHandle.createWritable();
                    await pdfWritable.write(file);
                    await pdfWritable.close();

                    const formData = new FormData();
                    formData.append("pdf", file);
                    const convertUrl = `${baseUrl}/api/convert-pdf`;
                    const response = await fetch(convertUrl, {
                        method: "POST",
                        body: formData,
                    });
                    const result = await response.json();

                    if (result.images) {
                        await Promise.all(
                            result.images.map(async (base64Image, index) => {
                                const imageName = `${fileName.split(".pdf")[0]}_${index + 1}.png`;
                                const imageHandle =
                                    await imageDir.getFileHandle(imageName, {
                                        create: true,
                                    });
                                const imageWritable =
                                    await imageHandle.createWritable();
                                const imageBlob = await (
                                    await fetch(base64Image)
                                ).blob();
                                await imageWritable.write(imageBlob);
                                await imageWritable.close();

                                const textResults =
                                    await extractTextFromImage(imageBlob);
                                const jsonHandle = await jsonDir.getFileHandle(
                                    `${imageName}.json`,
                                    { create: true },
                                );
                                const jsonWritable =
                                    await jsonHandle.createWritable();
                                await jsonWritable.write(
                                    JSON.stringify(textResults),
                                );
                                await jsonWritable.close();
                            }),
                        );
                    }
                } else {
                    const imageHandle = await imageDir.getFileHandle(fileName, {
                        create: true,
                    });
                    const imageWritable = await imageHandle.createWritable();
                    await imageWritable.write(file);
                    await imageWritable.close();

                    const textResults = await extractTextFromImage(file);
                    const jsonHandle = await jsonDir.getFileHandle(
                        `${fileName}.json`,
                        { create: true },
                    );
                    const jsonWritable = await jsonHandle.createWritable();
                    await jsonWritable.write(JSON.stringify(textResults));
                    await jsonWritable.close();
                }
                processedCount += 1;
            };

            const filePromises = fileHandles.map(processFile);
            await Promise.all(filePromises);
        } catch (err) {
            console.error("File upload error:", err);
        } finally {
            processingFiles = false;
        }
    }

    async function enrichFileData() {
        let selectorsNow = get(selectors);
        if (!selectorsNow.data) return [];

        let activeSelectorsNow = get(activeSelectors);
        let selectorsData = selectorsNow.data.selectors;
        const enrichedFiles = await Promise.all(
            $files.map(async (file) => {
                const jsonData = await loadJsonData(file.imageName);
                const foundTextMap: { [key: string]: string } = {};

                for (const selector of selectorsData) {
                    let hasTriggerText = false;
                    jsonData.analyzeResult.readResults[0].lines.forEach(
                        (line) => {
                            if (line.text.includes(selector.trigger_text)) {
                                hasTriggerText = true;
                            }
                        },
                    );

                    if (activeSelectorsNow[selector.id] && hasTriggerText) {
                        for (const anchor of selector.anchors) {
                            const anchorData = getAnchorData(anchor.id);
                            if (
                                anchorData &&
                                anchorData.radius &&
                                anchorData.dist_right &&
                                anchorData.dist_down &&
                                anchorData.column &&
                                anchorData.anchor_text
                            ) {
                                const {
                                    radius,
                                    dist_right,
                                    dist_down,
                                    column,
                                    anchor_text,
                                } = anchorData;

                                const lines =
                                    jsonData.analyzeResult.readResults[0].lines;
                                let anchor_text_result = lines.find((line) =>
                                    line.text.includes(anchor_text),
                                );
                                if (!anchor_text_result) {
                                    continue;
                                }
                                let anchor_text_bbox =
                                    anchor_text_result.boundingBox;

                                let anchor_text_bbox_center_x =
                                    (anchor_text_bbox[0] +
                                        anchor_text_bbox[4]) /
                                    2;
                                let anchor_text_bbox_center_y =
                                    (anchor_text_bbox[1] +
                                        anchor_text_bbox[5]) /
                                    2;

                                const circleX =
                                    anchor_text_bbox_center_x + dist_right;
                                const circleY =
                                    anchor_text_bbox_center_y + dist_down;

                                const foundTexts =
                                    jsonData.analyzeResult.readResults
                                        .flatMap(
                                            (readResult) => readResult.lines,
                                        )
                                        .filter((line) => {
                                            const [
                                                x1,
                                                y1,
                                                x2,
                                                y2,
                                                x3,
                                                y3,
                                                x4,
                                                y4,
                                            ] = line.boundingBox;
                                            const boxCenterX = (x1 + x3) / 2;
                                            const boxCenterY = (y1 + y3) / 2;

                                            return boxCenterIsInCircle(
                                                boxCenterX,
                                                boxCenterY,
                                                circleX,
                                                circleY,
                                                radius,
                                            );
                                        })
                                        .map((line) => line.text);

                                foundTextMap[column] = foundTexts.join(", ");
                            }
                        }
                    }
                }

                return { ...file, ...foundTextMap };
            }),
        );

        return enrichedFiles;
    }

    function downloadCSV() {
        const data = table.getData().map((row) => {
            const { name, pdfLink, imageLink, actions, ...dynamicData } = row;
            return { name, ...dynamicData };
        });

        const csvContent = [
            ["Name", ...get(dynamicColumns).map((col) => col)],
            ...data.map((row) => [
                row.name,
                ...get(dynamicColumns).map((col) => row[col] || ""),
            ]),
        ]
            .map((e) => e.join(","))
            .join("\n");

        const blob = new Blob([csvContent], {
            type: "text/csv;charset=utf-8;",
        });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", "files.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async function deleteAllFiles() {
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            const directories = ["images", "pdf", "json"];

            for (const directoryName of directories) {
                const dirHandle = await opfsRoot
                    .getDirectoryHandle(directoryName, { create: false })
                    .catch(() => null);
                if (dirHandle) {
                    for await (const [name, handle] of dirHandle.entries()) {
                        if (handle.kind === "file") {
                            await dirHandle.removeEntry(name);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Error deleting all files:", err);
        }
    }

    function handleDeleteAllFiles() {
        deleteAllFiles();
    }

    function cancelRemove() {
        showModal = false;
    }
</script>

<svelte:head>
    <link
        href="https://unpkg.com/tabulator-tables@6.2.3/dist/css/tabulator.min.css"
        rel="stylesheet"
    />
</svelte:head>

<Container header="Files">
    <Modal bind:open={showModal} size="xs" autoclose>
        <div slot="header">Confirm Deletion</div>
        Are you sure you want to delete these files forever?
        <div slot="footer">
            <Button on:click={handleDeleteAllFiles} color="red">Yes</Button>
            <Button on:click={cancelRemove} color="alternative">Cancel</Button>
        </div>
    </Modal>

    <div class="flex justify-between mb-2">
        <div class="flex items-center space-x-2">
            <Button on:click={handleFileUpload}>Add Files</Button>
            {#if processingFiles}
                <Spinner size="sm" />
                <span>{processedCount}/{totalCount} Complete</span>
            {/if}
        </div>
        <div class="flex items-center space-x-2">
            <Button on:click={() => (showModal = true)}>Delete All Files</Button
            >
            <Button on:click={downloadCSV}>Download CSV</Button>
        </div>
    </div>
    <div bind:this={tableComponent}></div>
</Container>
