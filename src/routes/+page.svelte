<script>
	import Files from "./Files.svelte";
	import Selectors from "./Selectors.svelte";
	import Viewer from "./Viewer.svelte";
</script>

<svelte:head>
	<title>Home</title>
	<meta name="description" content="Extract Text App" />
</svelte:head>

<a href="https://github.com/lectrician1/extract-text-app" class="absolute top-5 right-5">GitHub</a>
<div class="flex flex-row gap-10 m-16">
	<Files />
	<Selectors />
	<Viewer />
</div>
