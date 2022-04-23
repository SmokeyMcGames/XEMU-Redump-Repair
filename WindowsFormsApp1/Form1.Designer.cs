namespace XEMU_Redump_Repair
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Form1));
            this.button1 = new System.Windows.Forms.Button();
            this.openFileDialog1 = new System.Windows.Forms.OpenFileDialog();
            this.GameBox = new System.Windows.Forms.TextBox();
            this.button2 = new System.Windows.Forms.Button();
            this.GameLabel = new System.Windows.Forms.Label();
            this.ChosenGame = new System.Windows.Forms.Label();
            this.destBox = new System.Windows.Forms.TextBox();
            this.saveLoc = new System.Windows.Forms.Button();
            this.openFileDialog2 = new System.Windows.Forms.OpenFileDialog();
            this.label1 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.button3 = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // button1
            // 
            this.button1.Location = new System.Drawing.Point(13, 14);
            this.button1.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(147, 35);
            this.button1.TabIndex = 0;
            this.button1.Text = "Find ISO/XISO";
            this.button1.UseVisualStyleBackColor = true;
            this.button1.Click += new System.EventHandler(this.button1_Click);
            // 
            // openFileDialog1
            // 
            this.openFileDialog1.FileName = "openFileDialog1";
            // 
            // GameBox
            // 
            this.GameBox.Location = new System.Drawing.Point(168, 18);
            this.GameBox.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.GameBox.Name = "GameBox";
            this.GameBox.Size = new System.Drawing.Size(438, 26);
            this.GameBox.TabIndex = 1;
            // 
            // button2
            // 
            this.button2.Location = new System.Drawing.Point(220, 172);
            this.button2.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.button2.Name = "button2";
            this.button2.Size = new System.Drawing.Size(159, 57);
            this.button2.TabIndex = 2;
            this.button2.Text = "Repair";
            this.button2.UseVisualStyleBackColor = true;
            this.button2.Click += new System.EventHandler(this.button2_Click);
            // 
            // GameLabel
            // 
            this.GameLabel.AutoSize = true;
            this.GameLabel.Font = new System.Drawing.Font("Verdana", 12.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.GameLabel.ForeColor = System.Drawing.SystemColors.InfoText;
            this.GameLabel.Location = new System.Drawing.Point(171, 122);
            this.GameLabel.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.GameLabel.Name = "GameLabel";
            this.GameLabel.Size = new System.Drawing.Size(209, 32);
            this.GameLabel.TabIndex = 3;
            this.GameLabel.Text = "No ISO Loaded";
            // 
            // ChosenGame
            // 
            this.ChosenGame.AutoSize = true;
            this.ChosenGame.Font = new System.Drawing.Font("Microsoft Sans Serif", 14.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.ChosenGame.Location = new System.Drawing.Point(6, 120);
            this.ChosenGame.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.ChosenGame.Name = "ChosenGame";
            this.ChosenGame.Size = new System.Drawing.Size(175, 33);
            this.ChosenGame.TabIndex = 5;
            this.ChosenGame.Text = "File Loaded:";
            // 
            // destBox
            // 
            this.destBox.Location = new System.Drawing.Point(168, 63);
            this.destBox.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.destBox.Name = "destBox";
            this.destBox.Size = new System.Drawing.Size(438, 26);
            this.destBox.TabIndex = 6;
            // 
            // saveLoc
            // 
            this.saveLoc.Location = new System.Drawing.Point(13, 59);
            this.saveLoc.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.saveLoc.Name = "saveLoc";
            this.saveLoc.Size = new System.Drawing.Size(147, 35);
            this.saveLoc.TabIndex = 7;
            this.saveLoc.Text = "Save Location";
            this.saveLoc.UseVisualStyleBackColor = true;
            this.saveLoc.Click += new System.EventHandler(this.saveLoc_Click);
            // 
            // openFileDialog2
            // 
            this.openFileDialog2.FileName = "openFileDialog2";
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Microsoft Sans Serif", 8F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.ForeColor = System.Drawing.Color.Transparent;
            this.label1.Location = new System.Drawing.Point(428, 220);
            this.label1.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(186, 20);
            this.label1.TabIndex = 8;
            this.label1.Text = "BY: SmokeyMcGames";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(37, 176);
            this.label2.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(117, 20);
            this.label2.TabIndex = 9;
            this.label2.Text = "Support Me On";
            // 
            // button3
            // 
            this.button3.BackColor = System.Drawing.Color.Transparent;
            this.button3.Image = global::XEMU_Redump_Repair.Properties.Resources.yoas;
            this.button3.Location = new System.Drawing.Point(43, 196);
            this.button3.Name = "button3";
            this.button3.Size = new System.Drawing.Size(107, 41);
            this.button3.TabIndex = 10;
            this.button3.TextImageRelation = System.Windows.Forms.TextImageRelation.ImageAboveText;
            this.button3.UseVisualStyleBackColor = false;
            this.button3.Click += new System.EventHandler(this.button3_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(9F, 20F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.SystemColors.ActiveCaption;
            this.BackgroundImage = global::XEMU_Redump_Repair.Properties.Resources.prgramimage1;
            this.BackgroundImageLayout = System.Windows.Forms.ImageLayout.Center;
            this.ClientSize = new System.Drawing.Size(626, 243);
            this.Controls.Add(this.button3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.saveLoc);
            this.Controls.Add(this.destBox);
            this.Controls.Add(this.ChosenGame);
            this.Controls.Add(this.GameLabel);
            this.Controls.Add(this.button2);
            this.Controls.Add(this.GameBox);
            this.Controls.Add(this.button1);
            this.Cursor = System.Windows.Forms.Cursors.Default;
            this.DoubleBuffered = true;
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.Name = "Form1";
            this.Text = "XEMU Redump Repair";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Button button1;
        private System.Windows.Forms.OpenFileDialog openFileDialog1;
        private System.Windows.Forms.TextBox GameBox;
        private System.Windows.Forms.Button button2;
        private System.Windows.Forms.Label GameLabel;
        private System.Windows.Forms.Label ChosenGame;
        private System.Windows.Forms.TextBox destBox;
        private System.Windows.Forms.Button saveLoc;
        private System.Windows.Forms.OpenFileDialog openFileDialog2;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Button button3;
    }
}

