import {defineStore} from "pinia";
import {ref} from "vue";

export const useAdminInfoStore = defineStore('adminInfo',
    () => {
        const adminInfo = ref({})

        const setAdminInfo = (newAdminInfo) => {
            adminInfo.value = newAdminInfo
        }

        const removeAdminInfo = () => {
            adminInfo.value = {}
        }

        return {
            adminInfo, setAdminInfo, removeAdminInfo
        }
    },
    {
        persist: true
    });
