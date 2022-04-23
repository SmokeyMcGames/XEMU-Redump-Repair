using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Timers;

namespace XEMU_Redump_Repair
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }
        private void button1_Click(object sender, EventArgs e)
        {
            OpenFileDialog dialog = new OpenFileDialog();
            openFileDialog1.InitialDirectory = "C:";
            openFileDialog1.Title = "Choose Your ReDump";
            openFileDialog1.FileName = "";
            openFileDialog1.Filter = "ISO FILES|*.iso";

            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                GameLabel.Text = "" + openFileDialog1.SafeFileName + "";
                GameBox.Text = "" + openFileDialog1.FileName + "";
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            {
                OpenWithArguments();
            }
        }
        private void saveLoc_Click(object sender, EventArgs e)
        {
            SaveFileDialog saveFileDialog1 = new SaveFileDialog();
            saveFileDialog1.Filter = "ISO FILES| *.iso";
            saveFileDialog1.Title = "Save an Image File";
            saveFileDialog1.FileName = $"[Fixed]{GameLabel.Text}";

            if (saveFileDialog1.ShowDialog() == DialogResult.OK)
            {
                destBox.Text = saveFileDialog1.FileName;
            }
        }
        private static System.Timers.Timer aTimer;

        void OpenWithArguments()
        {
            string locAle = GameBox.Text;
            string desTin = destBox.Text;
            Process.Start("dd.exe", $"if={"\"" + locAle + "\""} of={"\"" + desTin + "\""} skip=387 bs=1M --progress");

            aTimer = new System.Timers.Timer();
            aTimer.Interval = 300;
            aTimer.Elapsed += OnTimedEvent;
            aTimer.AutoReset = false;
            aTimer.Enabled = true;

            void OnTimedEvent(Object source, System.Timers.ElapsedEventArgs e)
            {
                Process[] processes = Process.GetProcessesByName("dd");

                if (processes.Length == 1)
                {

                    MessageBox.Show("Something Went Wrong!", "Stopped", MessageBoxButtons.OK, MessageBoxIcon.None,
                    MessageBoxDefaultButton.Button1, (MessageBoxOptions)0x40000);
                }
                else
                {
                    MessageBox.Show("When The Command Window Closes Your Repair Is Complete!", "Converting..", MessageBoxButtons.OK, MessageBoxIcon.None,
                    MessageBoxDefaultButton.Button1, (MessageBoxOptions)0x40000);
                }
            }

            
        }

        private void button3_Click(object sender, EventArgs e)
        {
            string target = "https://www.youtube.com/smokeymcgames";
            System.Diagnostics.Process.Start(target);
        }
    }
}

