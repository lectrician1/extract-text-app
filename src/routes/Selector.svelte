<script lang="ts">
    import { writable, type Writable } from "svelte/store";
    import {
        Card,
        Label,
        Input,
        Checkbox,
        Button,
        Modal,
    } from "flowbite-svelte";
    import { CloseCircleOutline } from "flowbite-svelte-icons";
    import Anchor from "./Anchor.svelte";
    import {
        DeleteSelectorStore,
        InsertAnchorStore,
        UpdateSelectorStore,
    } from "$houdini";
    import { activeSelectors } from "./stores.ts";

    import type { GetSelectors$result } from "$houdini";

    type Selector = GetSelectors$result["selectors"][0];

    export let selector: Selector;

    // States for each section
    let selectorExpanded = writable(false);

    // States for checkboxes
    let checked = false;

    // State for the confirmation modal
    let showModal = writable(false);

    // Function to save the data
    const saveData = () => {
        let update = new UpdateSelectorStore();
        update.mutate({
            id: selector.id,
            _set: { name: selector.name, trigger_text: selector.trigger_text },
        });
    };

    // Function to toggle the collapse state
    const toggleSection = (section: Writable<boolean>) => {
        section.update((current) => !current);
    };

    function confirmRemove() {
        showModal.set(true);
    }

    function checkbox() {
        activeSelectors.update((selectors) => {
            selectors[selector.id] = checked;
            return selectors;
        });
    }

    function addAnchor() {
        let insertAnchorStore = new InsertAnchorStore();
        insertAnchorStore.mutate({ selector: selector.id });
    }

    function remove() {
        let deleteSelector = new DeleteSelectorStore();
        deleteSelector.mutate({ id: selector.id });
        showModal.set(false);
    }

    function cancelRemove() {
        showModal.set(false);
    }

    $: anchors = selector.anchors;
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<Card class="pd-8 relative">
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div class="absolute top-4 right-4 cursor-pointer" on:click={confirmRemove}>
        <CloseCircleOutline class="w-6 h-6 text-red-500" />
    </div>
    <!-- Confirmation Modal -->
    <Modal bind:open={$showModal} size="xs" autoclose>
        <div slot="header">Confirm Removal</div>
        Are you sure you want to remove this selector forever?
        <div slot="footer">
            <Button on:click={remove} color="red">Yes, Remove</Button>
            <Button on:click={cancelRemove} color="alternative">Cancel</Button>
        </div>
    </Modal>

    <!-- Header Section with Name Input -->
    <div class="header flex justify-between items-center">
        <div>
            <Label>Name</Label>
            <Input bind:value={selector.name} on:blur={saveData} />
        </div>
    </div>

    <!-- Active Checkbox and Collapse Link -->
    <div class="flex justify-between items-center mt-3">
        <Checkbox on:change={checkbox} bind:checked>Active</Checkbox>
        <a
            href="javascript:void(0)"
            class="text-blue-500"
            on:click={() => toggleSection(selectorExpanded)}
        >
            {#if $selectorExpanded}
                Collapse
            {:else}
                Expand
            {/if}
        </a>
    </div>

    {#if $selectorExpanded}
        <Label class="mt-3">Active if document contains</Label>
        <Input bind:value={selector.trigger_text} on:blur={saveData} />
        <h2 class="p-3 text-lg">Anchors</h2>
        <div class="ml-3 flex flex-col gap-2">
            {#each anchors as anchor (anchor.id)}
                <Anchor {anchor} />
            {/each}
            <Button on:click={addAnchor}>Add Anchor</Button>
        </div>
    {/if}
</Card>
