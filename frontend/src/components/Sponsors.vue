<template>
    <section id="sponsors">
        <div class="mt-20 text-center">
            <p class="max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-2xl md:max-w-3xl">
                A big thank you to our wonderful sponsors
            </p>
        </div>
        <div class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 flex items-center ">
            <div class="flex-auto grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-4 lg:gap-12 lg:mx-32">

                <Sponsor sponsor-name="Horizon Digital" sponsor-type="Major Sponsor" sponsor-url="https://horizondigital.au/" :sponsorImageUrl="horizonLogo" />

                <Sponsor sponsor-name="Ben Fitzhardinge" sponsor-type="Hosting Sponsor" sponsor-url="http://benjamin.dog/" :sponsorImageUrl="BenLogo" />

                <Sponsor sponsor-name="Spacecubed" sponsor-type="Venue Sponsor" sponsor-url="https://spacecubed.com/" :sponsorImageUrl="SpacecubedLogo" />

                <Sponsor sponsor-name="Gage Roads" sponsor-type="Beverage Sponsor" sponsor-url="https://gageroads.com.au/" :sponsorImageUrl="GageRoadsLogo" />

            </div>
        </div>
    </section>
</template>

<script>
import { ChatIcon } from "@heroicons/vue/outline";
import Sponsor from "./Sponsor.vue";
import HorizonLogo from "../assets/horizon_logo_sig.png";
import SpacecubedLogo from "../assets/spacecubed.png";
import BenLogo from "../assets/benjamin_dog.png";
import GageRoadsLogo from "../assets/gageroads_logo.png";
export default {
    components: {
      Sponsor,
      ChatIcon,
      HorizonLogo,
    },
  data() {
    return {
      horizonLogo: HorizonLogo,
      SpacecubedLogo,
      BenLogo,
      GageRoadsLogo,
    }
  }
};
</script> 