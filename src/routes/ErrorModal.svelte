<script>
    import { Modal } from "flowbite-svelte";
    import { errorStore } from "./stores";
</script>

{#if errorStore}
    <Modal size="xs" autoclose>
        <div slot="header">Error</div>
        <p>{$errorStore}</p>
    </Modal>
{/if}
