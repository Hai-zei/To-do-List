<template>
  <div class="todo-app">
    <div class="title">Todo App</div>

    <div class="todo-form">
      <input
        v-model="value"
        type="text"
        class="todo-input"
        placeholder="Add a todo"
      />
      <div @click="add" class="todo-button">Add Todo</div>
    </div>

    <div
      v-for="(item, index) in list"
      :key="index"
      :class="[item.isCompleted ? 'completed' : 'item']"
    >
      <div>
        <input @click="update(item.id)" v-model="item.isCompleted" type="checkbox" />
        <span class="name">{{ item.value }}</span>
      </div>

      <div @click="del(item.id)" class="del">del</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const value = ref('');
const list = ref([]);

// 从 localStorage 中获取数据
const getListFromLocalStorage = () => {
  const storedList = localStorage.getItem('todoList');
  if (storedList) {
    list.value = JSON.parse(storedList);
  }
};

// 将数据保存到 localStorage
const saveListToLocalStorage = () => {
  localStorage.setItem('todoList', JSON.stringify(list.value));
};

// 页面加载时从 localStorage 获取数据
onMounted(() => {
  getListFromLocalStorage();
});

const add = () => {
  if (value.value.trim() !== '') {
    const newItem = {
      id: Date.now(),
      value: value.value,
      isCompleted: false
    };
    list.value.push(newItem);
    saveListToLocalStorage();
    value.value = '';
  }
};

const update = (id) => {
  const item = list.value.find(item => item.id === id);
  if (item) {
    item.isCompleted = !item.isCompleted;
    saveListToLocalStorage();
  }
};

const del = (id) => {
  list.value = list.value.filter(item => item.id !== id);
  saveListToLocalStorage();
};
</script>

<style scoped>
.todo-app {
  box-sizing: border-box;
  margin-top: 40px;
  margin-left: 1%;
  padding-top: 30px;
  width: 98%;
  height: 500px;
  background: #ffffff;
  border-radius: 5px;
}

.title {
  text-align: center;
  font-size: 30px;
  font-weight: 700;
}

.todo-form {
  display: flex;
  margin: 20px 0 30px 20px;
}

.todo-button {
  width: 100px;
  height: 52px;
  border-radius: 0 20px 20px 0;

  text-align: center;
  background: linear-gradient(
    to right,
    rgb(113, 65, 168),
    rgba(44, 114, 251, 1)
  );
  color: #fff;
  line-height: 52px;
  cursor: pointer;
  font-size: 14px;
  user-select: none;
}

.todo-input {
  padding: 0px 15px 0px 15px;
  border-radius: 20px 0 0 20px;
  border: 1px solid #dfe1e5;
  outline: none;
  width: 60%;
  height: 50px;
}

.item {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 80%;
  height: 50px;
  margin: 8px auto;
  padding: 16px;
  border-radius: 20px;
  box-shadow: rgba(149, 157, 165, 0.2) 0px 8px 20px;
}

.del {
  color: red;
}

.completed {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 80%;
  height: 50px;
  margin: 8px auto;
  padding: 16px;
  border-radius: 20px;
  box-shadow: rgba(149, 157, 165, 0.2) 0px 8px 20px;
  text-decoration: line-through;
  opacity: 0.4;
}
</style>