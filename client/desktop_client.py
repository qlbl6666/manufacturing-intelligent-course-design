"""
工业缺陷智能检测系统 - C/S桌面客户端
基于 Tkinter + requests，调用后端 RESTful API
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
import io

# 后端服务地址
BASE_URL = "http://localhost:5000/api"


class LoginWindow:
    """登录窗口"""
    def __init__(self, root):
        self.root = root
        self.root.title("工业缺陷智能检测系统 - 登录")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5")

        self.session = requests.Session()
        self.token = None
        self.user = None

        self._build_ui()

    def _build_ui(self):
        # 标题
        title_frame = tk.Frame(self.root, bg="#1a3a5c", height=80)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🏭 工业缺陷智能检测系统",
                 font=("微软雅黑", 16, "bold"), fg="white", bg="#1a3a5c").pack(pady=20)

        # 表单
        form = tk.Frame(self.root, bg="#f0f2f5")
        form.pack(pady=30)

        tk.Label(form, text="用户名:", font=("微软雅黑", 11), bg="#f0f2f5").grid(row=0, column=0, pady=10, sticky="e")
        self.username_entry = tk.Entry(form, font=("微软雅黑", 11), width=20)
        self.username_entry.grid(row=0, column=1, pady=10, padx=10)
        self.username_entry.insert(0, "admin")

        tk.Label(form, text="密  码:", font=("微软雅黑", 11), bg="#f0f2f5").grid(row=1, column=0, pady=10, sticky="e")
        self.password_entry = tk.Entry(form, font=("微软雅黑", 11), width=20, show="*")
        self.password_entry.grid(row=1, column=1, pady=10, padx=10)
        self.password_entry.insert(0, "admin123")

        # 登录按钮
        login_btn = tk.Button(self.root, text="登 录", font=("微软雅黑", 12, "bold"),
                              bg="#2563eb", fg="white", width=15, height=1,
                              command=self.do_login, relief="flat", cursor="hand2")
        login_btn.pack(pady=10)

        # 提示
        tk.Label(self.root, text="默认账号: admin / admin123",
                 font=("微软雅黑", 9), fg="#888", bg="#f0f2f5").pack(pady=5)

        # 绑定回车
        self.password_entry.bind("<Return>", lambda e: self.do_login())

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        try:
            resp = self.session.post(f"{BASE_URL}/auth/login",
                                     json={"username": username, "password": password})
            data = resp.json()
            if data.get("success"):
                self.user = data.get("user")
                messagebox.showinfo("成功", f"欢迎回来，{self.user['username']}！")
                self.root.destroy()
                self._open_main()
            else:
                messagebox.showerror("失败", data.get("message", "登录失败"))
        except Exception as e:
            messagebox.showerror("错误", f"无法连接服务器: {e}\n请确保后端服务已启动")

    def _open_main(self):
        main_root = tk.Tk()
        MainWindow(main_root, self.session, self.user)
        main_root.mainloop()


class MainWindow:
    """主窗口"""
    def __init__(self, root, session, user):
        self.root = root
        self.session = session
        self.user = user
        self.current_image = None
        self.current_image_path = None

        self.root.title(f"工业缺陷智能检测系统 - {user['username']}")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        self.root.configure(bg="#f0f2f5")

        self._build_ui()
        self._load_stats()

    def _build_ui(self):
        # 顶部导航
        nav = tk.Frame(self.root, bg="#1a3a5c", height=50)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        tk.Label(nav, text="🏭 工业缺陷智能检测系统",
                 font=("微软雅黑", 14, "bold"), fg="white", bg="#1a3a5c").pack(side="left", padx=20)
        tk.Label(nav, text=f"用户: {self.user['username']} ({self.user.get('role', 'user')})",
                 font=("微软雅黑", 10), fg="#ccc", bg="#1a3a5c").pack(side="right", padx=20)

        # 标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.detect_frame = tk.Frame(notebook, bg="#f0f2f5")
        self.records_frame = tk.Frame(notebook, bg="#f0f2f5")
        self.stats_frame = tk.Frame(notebook, bg="#f0f2f5")

        notebook.add(self.detect_frame, text=" 🔍 缺陷检测 ")
        notebook.add(self.records_frame, text=" 📋 历史记录 ")
        notebook.add(self.stats_frame, text=" 📊 统计仪表盘 ")

        self._build_detect_tab()
        self._build_records_tab()
        self._build_stats_tab()

        # 底部状态栏
        status = tk.Frame(self.root, bg="#e0e0e0", height=25)
        status.pack(fill="x", side="bottom")
        status.pack_propagate(False)
        self.status_label = tk.Label(status, text="就绪", font=("微软雅黑", 9),
                                     bg="#e0e0e0", fg="#555", anchor="w")
        self.status_label.pack(side="left", padx=10)

    # ========== 检测标签页 ==========
    def _build_detect_tab(self):
        # 左侧：图片区域
        left = tk.Frame(self.detect_frame, bg="#f0f2f5")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        tk.Label(left, text="检测图片", font=("微软雅黑", 12, "bold"),
                 bg="#f0f2f5", fg="#1a3a5c").pack(anchor="w")

        self.image_canvas = tk.Canvas(left, bg="white", relief="solid", bd=1)
        self.image_canvas.pack(fill="both", expand=True, pady=5)
        self.image_canvas.create_text(200, 150, text="点击「选择图片」上传检测图片",
                                      fill="#999", font=("微软雅黑", 11))

        # 按钮区
        btn_frame = tk.Frame(left, bg="#f0f2f5")
        btn_frame.pack(fill="x", pady=5)

        tk.Button(btn_frame, text="📁 选择图片", font=("微软雅黑", 10),
                  bg="#2563eb", fg="white", command=self.select_image,
                  relief="flat", cursor="hand2", width=12).pack(side="left", padx=5)

        self.detect_btn = tk.Button(btn_frame, text="🚀 开始检测", font=("微软雅黑", 10, "bold"),
                                    bg="#16a34a", fg="white", command=self.do_detect,
                                    relief="flat", cursor="hand2", width=12, state="disabled")
        self.detect_btn.pack(side="left", padx=5)

        # 检测模式
        mode_frame = tk.Frame(left, bg="#f0f2f5")
        mode_frame.pack(fill="x", pady=5)
        tk.Label(mode_frame, text="检测模式:", font=("微软雅黑", 10), bg="#f0f2f5").pack(side="left")
        self.mode_var = tk.StringVar(value="precise")
        tk.Radiobutton(mode_frame, text="快速模式", variable=self.mode_var,
                       value="fast", bg="#f0f2f5", font=("微软雅黑", 9)).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="精确模式", variable=self.mode_var,
                       value="precise", bg="#f0f2f5", font=("微软雅黑", 9)).pack(side="left")

        # 右侧：结果区域
        right = tk.Frame(self.detect_frame, bg="white", relief="solid", bd=1, width=350)
        right.pack(side="right", fill="y", padx=10, pady=10)
        right.pack_propagate(False)

        tk.Label(right, text="检测结果", font=("微软雅黑", 12, "bold"),
                 bg="white", fg="#1a3a5c").pack(pady=10)

        self.result_text = tk.Text(right, font=("微软雅黑", 10), wrap="word",
                                   relief="flat", bg="#fafafa")
        self.result_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.result_text.insert("end", "等待检测...\n\n上传图片后点击「开始检测」")
        self.result_text.config(state="disabled")

    def select_image(self):
        path = filedialog.askopenfilename(
            title="选择检测图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")]
        )
        if path:
            self.current_image_path = path
            self.current_image = Image.open(path)
            self._show_image(self.current_image)
            self.detect_btn.config(state="normal")
            self.status_label.config(text=f"已选择: {os.path.basename(path)}")

    def _show_image(self, img):
        self.image_canvas.delete("all")
        canvas_w = self.image_canvas.winfo_width() or 400
        canvas_h = self.image_canvas.winfo_height() or 350

        img_copy = img.copy()
        img_copy.thumbnail((canvas_w - 20, canvas_h - 20))
        self.photo = ImageTk.PhotoImage(img_copy)

        x = (canvas_w - img_copy.width) // 2
        y = (canvas_h - img_copy.height) // 2
        self.image_canvas.create_image(x, y, anchor="nw", image=self.photo)

    def do_detect(self):
        if not self.current_image_path:
            return

        self.detect_btn.config(state="disabled")
        self.status_label.config(text="检测中，请稍候...")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "检测中，请稍候...")
        self.result_text.config(state="disabled")
        self.root.update()

        try:
            with open(self.current_image_path, "rb") as f:
                resp = self.session.post(
                    f"{BASE_URL}/detect/upload",
                    files={"image": f},
                    data={"mode": self.mode_var.get()}
                )
            data = resp.json()

            if data.get("success"):
                self._display_result(data)
                self.status_label.config(text="检测完成")
            else:
                messagebox.showerror("失败", data.get("message", "检测失败"))
                self.status_label.config(text="检测失败")
        except Exception as e:
            messagebox.showerror("错误", f"检测出错: {e}")
            self.status_label.config(text="检测出错")
        finally:
            self.detect_btn.config(state="normal")

    def _display_result(self, data):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")

        result = "✅ 正常" if data.get("is_normal") else "❌ 存在缺陷"
        lines = [
            f"检测结果: {result}",
            f"预测类别: {data.get('predicted_class_cn', '-')}",
            f"置信度: {data.get('confidence', 0):.2%}",
            f"缺陷数量: {data.get('defect_count', 0)}",
            f"检测模式: {'快速' if data.get('mode') == 'fast' else '精确'}",
            f"推理时间: {data.get('inference_time', 0):.2f}s",
            "",
            "=" * 30,
            "各类别概率:",
        ]

        class_names = {
            'crazing': '裂纹', 'inclusion': '夹杂', 'patches': '斑块',
            'pitted_surface': '麻点', 'rolled-in_scale': '氧化皮', 'scratches': '划痕'
        }
        probs = data.get("class_probabilities", {})
        for k, v in sorted(probs.items(), key=lambda x: -x[1]):
            lines.append(f"  {class_names.get(k, k)}: {v:.2%}")

        if data.get("detections"):
            lines.append("")
            lines.append("=" * 30)
            lines.append("缺陷详情:")
            for i, det in enumerate(data["detections"], 1):
                lines.append(f"  {i}. {det['class_name_cn']} (置信度: {det['confidence']:.2%})")

        self.result_text.insert("end", "\n".join(lines))
        self.result_text.config(state="disabled")

    # ========== 历史记录标签页 ==========
    def _build_records_tab(self):
        top = tk.Frame(self.records_frame, bg="#f0f2f5")
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="🔄 刷新", font=("微软雅黑", 10),
                  bg="#2563eb", fg="white", command=self._load_records,
                  relief="flat", cursor="hand2", width=10).pack(side="left", padx=5)

        # 表格
        columns = ("id", "time", "mode", "result", "defect_count", "class", "confidence")
        self.tree = ttk.Treeview(self.records_frame, columns=columns, show="headings", height=15)

        headings = [("id", "ID", 60), ("time", "检测时间", 160), ("mode", "模式", 80),
                    ("result", "结果", 80), ("defect_count", "缺陷数", 70),
                    ("class", "缺陷类型", 100), ("confidence", "置信度", 80)]
        for col, text, width in headings:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(self.records_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=0.98, rely=0.1, relheight=0.85)

        self._load_records()

    def _load_records(self):
        try:
            resp = self.session.get(f"{BASE_URL}/records", params={"page": 1, "per_page": 50})
            data = resp.json()
            self.tree.delete(*self.tree.get_children())

            for rec in data.get("records", []):
                self.tree.insert("", "end", values=(
                    rec["id"],
                    rec["created_at"][:19] if rec.get("created_at") else "-",
                    "快速" if rec.get("mode") == "fast" else "精确",
                    "正常" if rec.get("is_normal") else "有缺陷",
                    rec.get("defect_count", 0),
                    rec.get("predicted_class_cn", "-"),
                    f"{rec.get('confidence', 0):.1%}"
                ))
            self.status_label.config(text=f"共 {data.get('total', 0)} 条记录")
        except Exception as e:
            messagebox.showerror("错误", f"加载记录失败: {e}")

    # ========== 统计标签页 ==========
    def _build_stats_tab(self):
        self.stats_container = tk.Frame(self.stats_frame, bg="#f0f2f5")
        self.stats_container.pack(fill="both", expand=True, padx=10, pady=10)

    def _load_stats(self):
        try:
            resp = self.session.get(f"{BASE_URL}/stats/overview")
            data = resp.json()

            # 清除旧内容
            for w in self.stats_container.winfo_children():
                w.destroy()

            # 统计卡片
            cards_frame = tk.Frame(self.stats_container, bg="#f0f2f5")
            cards_frame.pack(fill="x", pady=10)

            cards = [
                ("总检测次数", data.get("total_detections", 0), "#2563eb"),
                ("缺陷样本数", data.get("defect_samples", 0), "#dc2626"),
                ("缺陷率", f"{data.get('defect_rate', 0):.1%}", "#f59e0b"),
                ("平均置信度", f"{data.get('avg_confidence', 0):.1%}", "#16a34a"),
            ]

            for i, (title, value, color) in enumerate(cards):
                card = tk.Frame(cards_frame, bg="white", relief="solid", bd=1)
                card.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
                cards_frame.grid_columnconfigure(i, weight=1)

                tk.Label(card, text=str(value), font=("微软雅黑", 24, "bold"),
                         fg=color, bg="white").pack(pady=10)
                tk.Label(card, text=title, font=("微软雅黑", 10),
                         fg="#666", bg="white").pack(pady=5)

            # 缺陷分布
            dist_frame = tk.Frame(self.stats_container, bg="white", relief="solid", bd=1)
            dist_frame.pack(fill="both", expand=True, pady=10)

            tk.Label(dist_frame, text="缺陷类型分布", font=("微软雅黑", 12, "bold"),
                     bg="white", fg="#1a3a5c").pack(anchor="w", padx=10, pady=10)

            dist = data.get("defect_distribution", {})
            class_names = {
                'crazing': '裂纹', 'inclusion': '夹杂', 'patches': '斑块',
                'pitted_surface': '麻点', 'rolled-in_scale': '氧化皮', 'scratches': '划痕',
                'normal': '正常'
            }

            max_val = max(dist.values()) if dist else 1
            for i, (k, v) in enumerate(sorted(dist.items(), key=lambda x: -x[1])):
                row = tk.Frame(dist_frame, bg="white")
                row.pack(fill="x", padx=20, pady=3)

                tk.Label(row, text=class_names.get(k, k), font=("微软雅黑", 10),
                         bg="white", width=10, anchor="w").pack(side="left")

                bar_w = int(v / max_val * 300) if max_val > 0 else 0
                bar = tk.Frame(row, bg="#2563eb", width=bar_w, height=20)
                bar.pack(side="left", padx=10)
                tk.Label(row, text=str(v), font=("微软雅黑", 10),
                         bg="white", fg="#333").pack(side="left")

        except Exception as e:
            tk.Label(self.stats_container, text=f"加载统计失败: {e}",
                     font=("微软雅黑", 11), fg="red", bg="#f0f2f5").pack(pady=20)


def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
