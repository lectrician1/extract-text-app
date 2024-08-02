<script lang="ts">
    import { Button } from "flowbite-svelte";
    import Selector from "./Selector.svelte";
    import Container from "./Container.svelte";

    import { InsertSelectorStore } from "$houdini";

    import { errorStore, selectors } from "./stores.ts";
    import { onMount } from "svelte";

    async function addSelector() {
        let insertSelector = new InsertSelectorStore()
        let response = await insertSelector.mutate({ name: "" , trigger_text: ""});
        if (response.errors) {
            errorStore.set(response.errors.toString())
        }
    }
    
    onMount(() => {
        selectors.listen()
    })

</script>

<Container header="Selectors">
    <div class="flex flex-col gap-4">
        {#if $selectors.data}
            {#each $selectors.data.selectors as selector (selector.id) }
                <Selector selector={selector}/>
            {/each}
        {/if}
        <Button on:click={addSelector}>Add Selector</Button>
    </div>
</Container>
