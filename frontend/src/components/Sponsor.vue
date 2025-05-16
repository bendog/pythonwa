<template>
  <div class="col-span-3 flex justify-center md:col-span-3 lg:col-span-2">
    <div class="flex grid grid-cols-1 items-center justify-center content-start">
      <div class="flex col-span-full items-center justify-center">
        <p class="font-medium text-gray-500">{{ sponsorType }}</p>
      </div>
      <div class="flex col-span-full items-center justify-center">
        <a :href="sponsorUrl">
            <img class="h-auto max-h-36 max-w-xs" :src="sponsorImageUrl" :alt="sponsorName" />
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Sponsor",
  props: ['sponsorName', 'sponsorType', 'sponsorUrl', 'sponsorImageUrl']
}
</script>

<style scoped>

</style>
