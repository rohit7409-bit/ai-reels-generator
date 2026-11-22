import os
import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
from security import hash_password, verify_password
from generator import make_text_content, make_reel_mp4

PROJECT_FACULTY = "Dr. Durga Puja, Mr. Pradeep Kumar Sharma, Mr. Malikhan Singh"


class ReelsStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Reels Generator — CSE Project")
        self.root.geometry("920x640")
        self.db = Database()
        self.user = None
        self.show_login()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def header(self, parent):
        ttk.Label(
            parent,
            text="B.S.A. College of Engg. & Tech., Mathura | B.Tech CSE Project",
            font=("Arial", 10, "bold"),
        ).pack()
        ttk.Label(
            parent,
            text=f"Project Faculty: {PROJECT_FACULTY}",
            font=("Arial", 9),
        ).pack(pady=(0, 10))

    def show_login(self):
        self.clear()
        f = ttk.Frame(self.root, padding=25)
        f.pack(expand=True)
        self.header(f)
        ttk.Label(f, text="AI Reels Generator", font=("Arial", 22, "bold")).pack(pady=10)

        ttk.Label(f, text="Email").pack(anchor="w")
        self.email = ttk.Entry(f, width=38)
        self.email.pack(pady=4)

        ttk.Label(f, text="Password").pack(anchor="w")
        self.password = ttk.Entry(f, width=38, show="*")
        self.password.pack(pady=4)

        ttk.Button(f, text="Login", command=self.login).pack(pady=8)
        ttk.Button(f, text="Register", command=self.show_register).pack()

    def login(self):
        user = self.db.get_user(self.email.get().strip())
        if not user or not verify_password(self.password.get(), user["password_hash"], user["password_salt"]):
            messagebox.showerror("Error", "Invalid email or password.")
            return
        self.user = user
        self.dashboard()

    def show_register(self):
        self.clear()
        f = ttk.Frame(self.root, padding=25)
        f.pack(expand=True)
        self.header(f)
        ttk.Label(f, text="Create Account", font=("Arial", 20, "bold")).pack(pady=10)

        entries = {}
        for name in ("Full Name", "Email", "Password"):
            ttk.Label(f, text=name).pack(anchor="w")
            e = ttk.Entry(f, width=38, show="*" if name == "Password" else "")
            e.pack(pady=4)
            entries[name] = e

        def save_user():
            if not all(entries[k].get().strip() for k in entries):
                messagebox.showwarning("Warning", "Please fill all fields.")
                return
            h, s = hash_password(entries["Password"].get())
            try:
                self.db.register_user(
                    entries["Full Name"].get().strip(),
                    entries["Email"].get().strip(),
                    h,
                    s,
                )
                messagebox.showinfo("Success", "Account created. Please login.")
                self.show_login()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        ttk.Button(f, text="Register", command=save_user).pack(pady=8)
        ttk.Button(f, text="Back", command=self.show_login).pack()

    def dashboard(self):
        self.clear()
        f = ttk.Frame(self.root, padding=25)
        f.pack(expand=True)
        self.header(f)
        ttk.Label(f, text=f"Welcome, {self.user['full_name']}", font=("Arial", 20, "bold")).pack(pady=15)
        ttk.Button(f, text="Create New Reel", command=self.create_reel).pack(pady=8)
        ttk.Button(f, text="My Reels & Export MP4", command=self.my_reels).pack(pady=8)
        ttk.Button(f, text="Logout", command=self.show_login).pack(pady=8)

    def create_reel(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill="both", expand=True)
        self.header(f)

        ttk.Label(f, text="Title").pack(anchor="w")
        title_e = ttk.Entry(f)
        title_e.pack(fill="x", pady=2)

        ttk.Label(f, text="Topic").pack(anchor="w")
        topic_e = ttk.Entry(f)
        topic_e.pack(fill="x", pady=2)

        ttk.Label(f, text="Script (Editable)").pack(anchor="w")
        script_t = tk.Text(f, height=5)
        script_t.pack(fill="x")

        ttk.Label(f, text="Caption").pack(anchor="w")
        cap_t = tk.Text(f, height=2)
        cap_t.pack(fill="x")

        ttk.Label(f, text="Hashtags").pack(anchor="w")
        tag_t = tk.Text(f, height=2)
        tag_t.pack(fill="x")

        def gen():
            t = topic_e.get().strip()
            if not t:
                messagebox.showwarning("Warning", "Please enter a topic first.")
                return
            res = make_text_content(t)
            script_t.delete("1.0", "end")
            script_t.insert("1.0", res["script"])
            cap_t.delete("1.0", "end")
            cap_t.insert("1.0", res["caption"])
            tag_t.delete("1.0", "end")
            tag_t.insert("1.0", res["hashtags"])

        def save():
            t = topic_e.get().strip()
            s = script_t.get("1.0", "end").strip()
            if not t or not s:
                messagebox.showwarning("Warning", "Topic and script are required.")
                return
            self.db.add_reel(
                self.user["id"],
                title_e.get().strip() or t,
                t,
                s,
                cap_t.get("1.0", "end").strip(),
                tag_t.get("1.0", "end").strip(),
            )
            messagebox.showinfo("Saved", "Reel saved.")
            self.my_reels()

        row = ttk.Frame(f)
        row.pack(pady=10)
        ttk.Button(row, text="Generate Content", command=gen).pack(side="left", padx=5)
        ttk.Button(row, text="Save Reel", command=save).pack(side="left", padx=5)
        ttk.Button(row, text="Back", command=self.dashboard).pack(side="left", padx=5)

    def my_reels(self):
        self.clear()
        f = ttk.Frame(self.root, padding=20)
        f.pack(fill="both", expand=True)
        self.header(f)

        cols = ("id", "title", "topic", "status", "output_path")
        tree = ttk.Treeview(f, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, pady=8)

        items = {}

        def refresh():
            tree.delete(*tree.get_children())
            items.clear()
            for r in self.db.get_reels(self.user["id"]):
                items[str(r["id"])] = r
                tree.insert("", "end", values=(r["id"], r["title"], r["topic"], r["status"], r["output_path"] or "-"))

        refresh()

        def render_video():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a reel first.")
                return
            rid = str(tree.item(sel[0])["values"][0])
            row = items[rid]
            try:
                out = make_reel_mp4(row["id"], row["title"], row["script"])
                self.db.set_video_path(row["id"], out)
                refresh()
                messagebox.showinfo("Success", f"Video saved:\n{out}")
                if os.name == "nt":
                    os.startfile(out)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        def delete_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a reel to delete.")
                return
            rid = int(tree.item(sel[0])["values"][0])
            self.db.delete_reel(rid, self.user["id"])
            refresh()

        row = ttk.Frame(f)
        row.pack(pady=8)
        ttk.Button(row, text="Export MP4", command=render_video).pack(side="left", padx=5)
        ttk.Button(row, text="Delete", command=delete_selected).pack(side="left", padx=5)
        ttk.Button(row, text="Back", command=self.dashboard).pack(side="left", padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    ReelsStudioApp(root)
    root.mainloop()
    