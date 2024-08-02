<script lang="ts">
    import { Button, Input, Label } from "flowbite-svelte";
    import { DeleteAnchorStore, UpdateAnchorStore, type GetSelectors$result } from "$houdini";
    import { selectedAnchor } from "./stores.ts";
    import { onMount, onDestroy } from 'svelte';

    type Anchor = GetSelectors$result['selectors'][0]['anchors'][0]

    export let anchor: Anchor;

    let isSelected = false;

    function remove() {
        let deleteAnchorStore = new DeleteAnchorStore();
        deleteAnchorStore.mutate({ id: anchor.id });
    }

    function saveData() {
        let anchorStore = new UpdateAnchorStore();
        anchorStore.mutate({ id: anchor.id, _set: anchor });
    }

    function handleSelect(event: MouseEvent) {
        if (!(event.target instanceof HTMLInputElement) && !(event.target instanceof HTMLButtonElement)) {
            selectedAnchor.set(anchor.id);
        }
    }

    const unsubscribe = selectedAnchor.subscribe(value => {
        isSelected = value === anchor.id;
    });

    onMount(() => {
        document.addEventListener('click', handleClickOutside);
    });

    onDestroy(() => {
        unsubscribe();
        document.removeEventListener('click', handleClickOutside);
    });

    function handleClickOutside(event: MouseEvent) {
        const clickedAnchor = event.composedPath().find(element => element instanceof HTMLElement && element.id && element.id.startsWith('anchor-'));
        if (isSelected && clickedAnchor && clickedAnchor.id !== `anchor-${anchor.id}`) {
            selectedAnchor.set(null);
        }
    }
</script>

<div
    id="anchor-{anchor.id}"
    class="flex flex-col gap-2 relative border-4 border-current p-5 rounded-xl"
    class:bg-orange-500={isSelected}
    on:click={handleSelect}
>
    <div class="absolute top-1 right-2">
        <Button size="sm" color="failure" on:click={remove}>X</Button>
    </div>
    <Label>Column Name</Label>
    <Input bind:value={anchor.column} on:blur={saveData}/>
    <Label>Anchor text</Label>
    <Input bind:value={anchor.anchor_text} on:blur={saveData}/>
    <Label>Distance right</Label>
    <Input bind:value={anchor.dist_right} on:blur={saveData}/>
    <Label>Distance down</Label>
    <Input bind:value={anchor.dist_down} on:blur={saveData}/>
    <Label>Radius</Label>
    <Input bind:value={anchor.radius} on:blur={saveData}/>
</div>
