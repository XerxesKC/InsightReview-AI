import {defineStore} from "pinia";
import {ref} from "vue";

export const useMerchantInfoStore = defineStore('userInfo',
    () => {
        const merchantInfo = ref({})

        const setMerchantInfo = (newMerchantInfo) => {
            merchantInfo.value = newMerchantInfo
        }

        const removeMerchantInfo = () => {
            merchantInfo.value = {}
        }

        return {
            merchantInfo, setMerchantInfo, removeMerchantInfo
        }
    },
    {
        persist: true
    });
