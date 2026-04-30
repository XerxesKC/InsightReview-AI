import axios from "axios";
import {ElMessage} from "element-plus";
import router from "@/router";

const instance = axios.create();

instance.interceptors.request.use(
    config => {
        if (!config.baseURL && typeof config.url === "string" && config.url.startsWith("/api/v1")) {
            config.baseURL = "http://127.0.0.1:8001"
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

instance.interceptors.response.use(
    result => {
        const data = result.data;
        if (
            data.code === 0 ||
            data.code === 200 ||
            !("code" in data) ||
            data.success === true
        ) {
            return data;
        }

        return Promise.reject(data);
    },
    error => {
        if (error.response && error.response.status === 70005) {
            ElMessage.error("请先登录")
            router.push('/login')
        }
        return Promise.reject(error)
    }
)

export default instance
