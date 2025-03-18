<script setup>
import {defineProps,defineEmits} from 'vue'

const props = defineProps(['text'])
const emit = defineEmits(['ok'])

function send(){

    emit('ok','hello')
}
</script>

<template>
    <div @click="send" class="button">{{ props.text }}</div>
</template>

<style scoped>
.button{
    margin: 100px 0 0 200px;
    width: 100px;
    height: 50px;
    line-height: 50px;
    text-align: center;
    background-color: antiquewhite;
    border-radius: 10px;
}
</style>