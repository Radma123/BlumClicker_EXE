import cv2
import numpy as np
import pyautogui
from pynput import keyboard
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random
import tkinter as tk
from PIL import Image, ImageTk

# Диапазон смещения курсора от центра снежинки вниз
RAND_MIN = 5
RAND_MAX = 10

# Кнопка активации/деактивации кликера
ACTIVE_BTN = keyboard.Key.ctrl_r
# Кнопка завершения программы
EXIT_BTN = keyboard.Key.backspace

# Параметры захвата экрана
region = (900, 550, 370, 530)
element_lower = np.array([45, 75, 75])
element_upper = np.array([75, 255, 255])

# Диапазоны для темно-зеленого цвета
dark_green_lower = np.array([6, 22, 0])
dark_green_upper = np.array([85, 255, 125])

# Минимальная и максимальная площадь контура для фильтрации
min_contour_area = 150
max_contour_area = 1000

clicking_enabled = False
program_running = True
executor = ThreadPoolExecutor(max_workers=10)  # Пул потоков

def on_press(key):
    global clicking_enabled, program_running
    try:
        if key == ACTIVE_BTN:
            if not clicking_enabled:
                button_status.config(text="ON", bg="green", fg="white", font=("Arial", 20))
            else:
                button_status.config(text="OFF", bg="red", fg="white", font=("Arial", 20))
            clicking_enabled = not clicking_enabled
            print(f"Clicking enabled: {clicking_enabled}")
        elif key == EXIT_BTN:
            program_running = False
            print("Exiting program...")
            return False  # Останавливает слушатель клавиш
    except AttributeError:
        pass

def process_frame(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, element_lower, element_upper)
    
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    filtered_contours = []
    for i, cnt in enumerate(contours):
        if min_contour_area <= cv2.contourArea(cnt) <= max_contour_area and hierarchy[0][i][3] == -1:
            filtered_contours.append(cnt)
    return filtered_contours

def click_on_position(screen_x, screen_y):
    if clicking_enabled:
        pyautogui.click(screen_x, screen_y + random.randint(RAND_MIN, RAND_MAX))

def click_element_contours(contours):
    global clicking_enabled
    for cnt in contours:
        if not clicking_enabled:
            break
        (x, y, w, h) = cv2.boundingRect(cnt)
        center_x = x + w // 2
        center_y = y + h // 2
        screen_x = region[0] + center_x
        screen_y = region[1] + center_y
        executor.submit(click_on_position, screen_x, screen_y)

def capture_and_process():
    global program_running
    while program_running:
        screenshot = pyautogui.screenshot(region=region)
        frame_tk = np.array(screenshot)
        frame = cv2.cvtColor(frame_tk, cv2.COLOR_RGB2BGR)

        contours = process_frame(frame)

        # Удаляем темно-зеленый цвет
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        dark_green_mask = cv2.inRange(hsv_frame, dark_green_lower, dark_green_upper)
        frame[dark_green_mask > 0] = (0, 0, 0)

        cv2.drawContours(frame, contours, -1, (0, 0, 255), 2)

        # вывод tkinter
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        image_tk = ImageTk.PhotoImage(image)
        label.imgtk = image_tk  # Сохраняем ссылку на изображение
        label.config(image=image_tk)

        root.update()

        if clicking_enabled:
            time.sleep(0.04)
            click_element_contours(contours)
        else:
            time.sleep(0.2)


    print("Capture and processing thread terminated")
    stop_all()

def stop_all():
    global program_running
    program_running = False
    root.quit()  # Завершаем работу окна tkinter
    print("Program fully stopped")

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    capture_thread = threading.Thread(target=capture_and_process)
    capture_thread.start()

    root = tk.Tk()
    root.resizable(False, False)
    root.title("Blum_Clicker")
    root.geometry("370x660+1400+300")

    label = tk.Label(root)
    label.pack(side='bottom')

    label_with_bg = tk.Label(root,
                            text="Нажмите правый Ctrl, чтобы начать или закончить",
                            bg="blue",
                            fg="white",
                            font=("Arial", 18),
                            wraplength=320)
    button_status = tk.Button(root,
                            text="OFF",
                            bg="red",
                            fg="white",
                            font=("Arial", 20),
                            wraplength=220,
                            command= lambda: on_press(keyboard.Key.ctrl_r))
                             
    label_status = tk.Label(root,
                            text="OFF",
                            bg="red",
                            fg="white",
                            font=("Arial", 20),
                            wraplength=220)
    label_backspace = tk.Label(root,
                               text="Выйти = Backspace",
                               bg="black",
                               fg="white",
                               font=("Arial", 13),)
    
    label_backspace.pack(side='top',fill="x")
    label_with_bg.pack(side='left',fill='both')
    # label_status.pack(side='right',fill='both')
    button_status.pack(side='right',fill='both')

    

    # Добавляем обработчик закрытия окна
    root.protocol("WM_DELETE_WINDOW", stop_all)

    root.mainloop()