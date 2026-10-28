# -*- coding: utf-8 -*-
"""
HTML-to-PDF Generator for Detecta Viva Defense Cheat Sheet
Produces a clean, compact 2-3 page document with 100% perfect Bengali and English rendering.
"""
import os

html_content = r'''<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="utf-8">
<title>Detecta: Project Defense & Viva Quick Guide</title>
<style>
  @page {
    size: letter;
    margin: 10mm 12mm 10mm 12mm;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    font-family: 'Segoe UI', 'Nirmala UI', 'Kalpurush', Tahoma, Arial, sans-serif;
    color: #0f172a;
    background: #ffffff;
    font-size: 11px;
    line-height: 1.38;
  }
  .header-card {
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 6px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }
  .header-title h1 {
    font-size: 16px;
    color: #1e3a8a;
    font-weight: 800;
    line-height: 1.2;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .header-title h2 {
    font-size: 11.5px;
    color: #2563eb;
    font-weight: 600;
    margin-top: 2px;
  }
  .meta-badge {
    text-align: right;
    font-size: 9.5px;
    color: #475569;
    line-height: 1.35;
  }
  .meta-badge strong {
    color: #0f172a;
  }
  
  .section {
    margin-bottom: 8px;
  }
  .section-title {
    font-size: 11.5px;
    font-weight: 700;
    color: #1e3a8a;
    border-left: 3.5px solid #2563eb;
    padding-left: 6px;
    margin-bottom: 4px;
    background: #f1f5f9;
    padding-top: 2px;
    padding-bottom: 2px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  /* Callout Speech Box */
  .callout-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 6px;
  }
  .callout-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #3b82f6;
    border-radius: 4px;
    padding: 6px 8px;
  }
  .callout-box.en {
    border-left-color: #10b981;
  }
  .callout-header {
    font-weight: 700;
    font-size: 10px;
    color: #1e3a8a;
    margin-bottom: 3px;
    display: flex;
    justify-content: space-between;
  }
  .callout-box.en .callout-header {
    color: #047857;
  }
  .speech-text {
    font-size: 10px;
    line-height: 1.35;
    color: #1e293b;
    font-style: italic;
  }

  /* Grid 2-column layout */
  .grid-2 {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 8px;
  }

  /* Feature cards */
  .card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 6px 8px;
    margin-bottom: 5px;
  }
  .card-title {
    font-weight: 700;
    color: #0f172a;
    font-size: 10.5px;
    margin-bottom: 2px;
  }
  .card-title span {
    color: #2563eb;
    font-size: 9.5px;
    font-family: Consolas, monospace;
  }
  .card p {
    font-size: 10px;
    color: #334155;
    line-height: 1.35;
  }

  /* Q&A Compact List */
  .qa-item {
    margin-bottom: 5px;
    padding-bottom: 4px;
    border-bottom: 1px dashed #e2e8f0;
  }
  .qa-q {
    font-weight: 700;
    color: #1e3a8a;
    font-size: 10.5px;
    margin-bottom: 1.5px;
  }
  .qa-a {
    font-size: 10px;
    color: #1e293b;
    line-height: 1.35;
    padding-left: 8px;
    border-left: 2px solid #94a3b8;
  }

  /* Table styling */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5px;
    margin-top: 3px;
  }
  th {
    background: #1e3a8a;
    color: #ffffff;
    text-align: left;
    padding: 3px 6px;
    font-weight: 600;
  }
  td {
    padding: 2.5px 6px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
  }
  tr:nth-child(even) {
    background: #f8fafc;
  }
  .badge {
    display: inline-block;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 8.5px;
    font-weight: 600;
    background: #e2e8f0;
    color: #334155;
  }
  .badge-success { background: #dcfce7; color: #166534; }
  .badge-primary { background: #dbeafe; color: #1e40af; }

  .page-break {
    page-break-before: always;
  }
  .footer-note {
    text-align: center;
    font-size: 8.5px;
    color: #64748b;
    margin-top: 6px;
    border-top: 1px solid #cbd5e1;
    padding-top: 3px;
  }
</style>
</head>
<body>

  <!-- ================= PAGE 1 ================= -->
  <div class="header-card">
    <div class="header-title">
      <h1>Detecta &mdash; Viva Defense & Quick Guide</h1>
      <h2>Smart AI Surveillance Camera with Multi-Modal Vision & Edge IoT</h2>
    </div>
    <div class="meta-badge">
      <strong>Presenter:</strong> Ahmmed Waseg Bin Mizan Orgho (ID: 251031046)<br>
      <strong>Role:</strong> Software Lead &nbsp;|&nbsp; <strong>Course:</strong> CSE-214 &nbsp;|&nbsp; Feni University
    </div>
  </div>

  <!-- SECTION 1: 1-MINUTE ELEVATOR PITCH -->
  <div class="section">
    <div class="section-title">১. ১-মিনিট এলিভেটর পিচ (ম্যামের সামনে ওপেনিং স্পিচ &mdash; মুখস্থ বলার জন্য)</div>
    <div class="callout-grid">
      <div class="callout-box">
        <div class="callout-header">
          <span>🗣️ বাংলা ডায়ালগ (Oral Presentation)</span>
          <span class="badge badge-primary">বাংলা</span>
        </div>
        <div class="speech-text">
          &ldquo;আসসালামু আলাইকুম ম্যাম। আমাদের প্রজেক্ট <b>Detecta</b> একটি এজ-টু-ওয়ার্কস্টেশন স্মার্ট এআই সার্ভিল্যান্স ক্যামেরা। প্রজেক্টে আমার মূল দায়িত্ব ছিল <b>Software Lead</b> হিসেবে&mdash;মাল্টি-মোডাল এআই ইঞ্জিন, হাই-স্পিড স্ট্রিমিং ও ব্যাকএন্ড ডেভেলপমেন্ট।<br>
          আমরা ওয়্যারলেস <b>ESP32-CAM</b> থেকে ডেডিকেটেড Port 81-এ ভিডিও স্ট্রিম নিয়ে লোকাল <b>RTX 4050 GPU</b> তে ৩টি এআই মডেল একসাথে চালাচ্ছি: <b>YOLO11s</b> (২১টি অবজেক্ট), <b>InsightFace ArcFace 512-D</b> (ফেস ভেরিফিকেশন), এবং <b>MediaPipe Hands</b> (৭টি জেসচার)। এছাড়া খালি আঙুলকে কলম ভাবা রোধে আমরা নিজস্ব <b>Smart Spatial Pen Filter</b> বানিয়েছি। সম্পূর্ণ সিস্টেমটি লোকাল ড্যাশবোর্ড ও নেটিভ উইন্ডোজ অ্যাপ (<b>Detecta.exe</b>) হিসেবে কোনো ক্লাউড ছাড়াই টানা <b>২০&ndash;২৫+ FPS</b> এ চলে।&rdquo;
        </div>
      </div>

      <div class="callout-box en">
        <div class="callout-header">
          <span>🗣️ English Pitch (If Evaluator Prefers English)</span>
          <span class="badge badge-success">English</span>
        </div>
        <div class="speech-text">
          &ldquo;Respected Ma'am, our project <b>Detecta</b> decouples edge IoT capture from local GPU computing. I served as the <b>Software Lead</b>, developing the multi-modal AI engine, high-speed ingestion pipeline, and backend.<br>
          An untethered <b>ESP32-CAM</b> streams VGA MJPEG over dedicated Port 81. On our workstation GPU (RTX 4050), we execute three concurrent pipelines: <b>Ultralytics YOLO11s</b> (21 curated classes), <b>InsightFace ArcFace 512-D biometrics</b> (with 25-frame stride caching), and <b>MediaPipe Hands</b> with spatial pen disambiguation. The system sustains <b>20&ndash;25+ FPS</b> with sub-50ms latency via FastAPI and a native desktop app (<b>Detecta.exe</b>) with zero cloud dependency.&rdquo;
        </div>
      </div>
    </div>
  </div>

  <!-- SECTION 2 & 3: ARCHITECTURE & SOFTWARE DEEP-DIVE -->
  <div class="section">
    <div class="section-title">২. সফটওয়্যার আর্কিটেকচার ও মূল ইনোভেশন (Software Lead Core Contributions)</div>
    <div class="grid-2">
      <div>
        <div class="card">
          <div class="card-title">১. OpenCV সকেট ডেডলক বাইপাস <span>(camera_stream.py)</span></div>
          <p>• <b>সমস্যা:</b> সাধারণ <code>cv2.VideoCapture</code> ওয়াই-ফাই নেটওয়ার্কের প্যাকেট জিটারে সকেট ব্লক করে ভিডিও ফ্রিজ করে ফেলে।<br>
          • <b>সমাধান:</b> পাইথনের <code>requests</code> দিয়ে মেমোরি থেকে সরাসরি JPEG SOI (<code>0xFFD8</code>) ও EOI (<code>0xFFD9</code>) বাউন্ডারি স্লাইস করে জিরো-ল্যাগ স্ট্রিমিং ও অ্যাটমিক বাফারিং নিশ্চিত করা হয়েছে।</p>
        </div>
        <div class="card">
          <div class="card-title">২. YOLO11s অবজেক্ট ও কার্টন ডিটেকশন <span>(ai_engine.py)</span></div>
          <p>• <b>CUDA FP16 ইনফারেন্স:</b> ২১টি কিউরেটেড ক্লাস (মানুষ, ল্যাপটপ, ফোন, কলম, বই ইত্যাদি) মাত্র <b>১১.৪ms</b> লেটেন্সিতে ডিটেক্ট হয়।<br>
          • <b>বক্স ও পার্সেল হ্যান্ডলিং:</b> ক্লাস ২৪, ২৬ ও ২৮ কে টিউন করে ডেলিভারি ও স্টোরেজ কার্টন নিখুঁতভাবে ডিটেক্ট করা হয়েছে।<br>
          • <b>EMA ফিল্টার:</b> বাউন্ডিং বক্স যাতে না কাঁপে, সেজন্য Exponential Moving Average (&alpha;=0.65, TTL=6) ব্যবহার করা হয়েছে।</p>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-title">৩. ArcFace 512-D ও ২৫-ফ্রেম স্ট্রাইড ক্যাশিং <span>(ai_engine.py)</span></div>
          <p>• <b>Dlib বনাম ArcFace:</b> Dlib ১২৮-D ভেক্টর তৈরি করে এবং অ্যাঙ্গেলে ফেস মিস করে। ArcFace ৫১২-D ভেক্টর ও কোসাইন সিমিলারিটি দেয়।<br>
          • <b>🔥 ২৫-ফ্রেম স্ট্রাইড উদ্ভাবন:</b> প্রতি ফ্রেমে ফেস মডেল ৩৮ms সময় নেয়। আমরা একবার ফেস ভেরিফাই করে পরবর্তী ২৫ ফ্রেমের জন্য আইডি ক্যাশ রাখি। ফলে গড় লেটেন্সি <b>&lt;২ms</b> এ নেমে আসে এবং FPS থাকে <b>২০&ndash;২৫+</b>!</p>
        </div>
        <div class="card">
          <div class="card-title">৪. স্মার্ট পেন ডিসঅ্যাম্বিগিউয়েশন অ্যালগরিদম <span>(ai_engine.py)</span></div>
          <p>• <b>সমস্যা:</b> খালি তর্জনী আঙুল দেখালে এআই প্রায়ই বিভ্রান্ত হয়ে কলম (Pen) হিসেবে ডিটেক্ট করে ফেলে।<br>
          • <b>আমাদের সমাধান:</b> মিডিয়াপাইপ হ্যান্ড বাউন্ডারি চেক করা হয়। আঙুলের মাথা ছাড়িয়ে কোনো বাস্তব বস্তু অন্তত <b>২৫ পিক্সেল বাইরে প্রসারিত</b> থাকলেই কেবল তা <code>Pen [Held]</code> হিসেবে ভেরিফাই হয়; খালি আঙুল স্বয়ংক্রিয়ভাবে বাতিল হয়।</p>
        </div>
        <div class="card">
          <div class="card-title">৫. সিঙ্গল-পাস ক্যাশিং ও উইন্ডোজ অ্যাপ <span>(backend.py / Detecta.exe)</span></div>
          <p>• <b>FastAPI Single-Pass Cache:</b> ব্যাকগ্রাউন্ড থ্রেডে ফ্রেমটি একবারই এনকোড হয়ে মেমোরিতে থাকে; সব ক্লায়েন্ট এক ক্যাশ থেকে স্ট্রিম নেয় (CPU লোড ৭০% কম)।<br>
          • <b>নেটিভ ডেক্সটপ অ্যাপ:</b> Microsoft Edge WebView2 ইঞ্জিন দিয়ে তৈরি স্ট্যান্ডঅ্যালোন <code>Detecta.exe</code> অ্যাপ।</p>
        </div>
      </div>
    </div>
  </div>

  <!-- SECTION 3: QUICK HARDWARE SUMMARY -->
  <div class="section">
    <div class="section-title">৩. হার্ডওয়্যার সার্কিটের মূল পয়েন্ট (ম্যাম হার্ডওয়্যার জিজ্ঞাসা করলে)</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
      <div class="card" style="margin-bottom: 0;">
        <p>• <b>18650 Li-ion ব্যাটারি (3.7V):</b> পোর্টেবল পাওয়ার সোর্স (৩.০V কাট-অফ থেকে ৪.২V ফুল চার্জ)।<br>
        • <b>IP2312 3A Type-C ফাস্ট চার্জার:</b> সিঙ্ক্রোনাস বাক চার্জার (>৯২% এফিশিয়েন্সি), ৩A রেটিং। সাধারণ TP4056 এর মতো গরম হয় না।<br>
        • <b>SPST সুইচ:</b> ব্যাটারি পজিটিভ লাইনে ইন-লাইন বসানো; স্ট্যান্ডবাই ড্রেন শূন্য করে।</p>
      </div>
      <div class="card" style="margin-bottom: 0;">
        <p>• <b>XL6009 4A বুস্ট কনভার্টার:</b> ব্যাটারির ৩.৭V কে স্টেপ-আপ করে স্থির <b>5.0V DC</b> দেয়। W103 (10k) ট্রিমার দিয়ে টিউন করা, যা ESP32 ব্রাউন-আউট বন্ধ করে।<br>
        • <b>রেজিস্টর ডিভাইডার ও Pin 4:</b> ৫V ও GND এর মাঝে সিরিজে দুটি রেজিস্টর দিয়ে মিডপয়েন্ট <b>Pin 4 (GPIO 4 / ADC)</b> এ নেওয়া হয়েছে, যা নিরাপদে ৩.৩V এর মধ্যে ব্যাটারি ভোল্টেজ মাপে।<br>
        • <b>ESP32-CAM পিনআউট:</b> Pin 1 (5V VCC), Pin 2 (GND), Pin 4 (ADC ট্যাপ)।</p>
      </div>
    </div>
  </div>

  <!-- ================= PAGE 2 ================= -->
  <div class="page-break"></div>

  <div class="header-card">
    <div class="header-title">
      <h1>Detecta &mdash; Viva Q&amp;A Defense &amp; Technical Specs</h1>
      <h2>ম্যামের সম্ভাব্য ১০টি কঠিন ভাইভা প্রশ্ন ও স্পেসিফিকেশন চিট-শীট</h2>
    </div>
    <div class="meta-badge">
      Software Lead: Ahmmed Waseg (251031046)<br>
      Page 2 of 2
    </div>
  </div>

  <!-- SECTION 4: VIVA Q&A DEFENSE -->
  <div class="section">
    <div class="section-title">৪. ম্যামের সম্ভাব্য ৮টি কঠিন প্রশ্ন ও আপনার মোক্ষম উত্তর (Viva Defense Cheat Sheet)</div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ১: ESP32-CAM ওয়াই-ফাইতে কানেক্ট হওয়ার সময় বা স্ট্রিমিং করার সময় হঠাৎ রিস্টার্ট দিত? কীভাবে সলভ করেছ?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, Wi-Fi RF ট্রান্সমিট করার সময় প্রায় ৪৫০mA কারেন্ট স্পাইক হয়, যার ফলে লো-ভোল্টেজ ড্রপ হয়ে ইন্টারনাল RTC ব্রাউনআউট রিস্টার্ট দিত। আমরা দুটি স্টেপে এটি সলভ করেছি: (১) হার্ডওয়্যারে আমরা হাই-কারেন্ট <b>XL6009 4A বুস্ট কনভার্টার</b> দিয়ে ভোল্টেজকে ৫.০V এ লক করেছি; (২) সফটওয়্যারে <code>main.cpp</code>-এর শুরুতে রেজিস্টার লেভেলে ব্রাউনআউট ডিটেক্টর ডিসেবল করেছি: <code>WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);</code>। এরপর থেকে সিস্টেম সম্পূর্ণ স্টেবল।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ২: ভিডিও স্ট্রিমে এত হাই ফ্রেমরেট (20&ndash;25+ FPS) কীভাবে পেলে? সাধারণত তো ৮-১০ FPS এর বেশি ওঠে না!</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, ৩টি অপ্টিমাইজেশন করেছি: (১) ESP32-CAM এ 4MB PSRAM দিয়ে <b>ডুয়াল ফ্রেমবাফারিং</b> (<code>CAMERA_FB_IN_PSRAM, fb_count = 2</code>) করেছি, ফলে এক ফ্রেম ট্রান্সমিট হওয়ার সময় পরবর্তী ফ্রেম মেমোরিতে রেডি থাকে; (২) OpenCV-এর ব্লকিং সকেট বাইপাস করে নিজস্ব মাল্টি-থ্রেডেড পাইথন চাঙ্ক পার্সার লিখেছি; (৩) এআই ইঞ্জিনে <b>২৫-ফ্রেম স্ট্রাইড ভেরিফিকেশন ক্যাশ</b> ব্যবহার করায় প্রতি ফ্রেমে ভারী ফেস মডেল রান হয় না, ফলে গড় লেটেন্সি মাত্র ১-২ms এ নেমে এসেছে।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৩: Dlib ব্যবহার না করে InsightFace ArcFace কেন ব্যবহার করেছ?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, Dlib এর মডেলটি পুরনো (১২৮-D ভেক্টর) এবং ইউক্লিডিয়ান ডিসটেন্স নির্ভর। মুখ সামান্য বাঁকা থাকলে বা কম আলোতে Dlib ফেস মিস করে। পক্ষান্তরে, <b>ArcFace</b> একটি ডিপ কনভোল্যুশনাল মডেল যা <b>৫১২-ডাইমেনশনাল হাইপার-স্ফেয়ারিক্যাল ফিচার ভেক্টর</b> তৈরি করে এবং ৫-পয়েন্ট ল্যান্ডমার্ক অ্যালাইনমেন্টের পর কোসাইন সিমিলারিটি দিয়ে ম্যাচ করায় এর নির্ভুলতা ৯৯.৮% এর বেশি।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৪: খালি আঙুল দেখালে কলম যেন না ভাবে, এই অ্যালগরিদমটা কীভাবে কাজ করে?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, আমরা YOLO এর পেন বক্সের সাথে MediaPipe এর হ্যান্ড ল্যান্ডমার্কের স্প্যাশিয়াল ইন্টারসেকশন মিলিয়েছি। যদি পেন বক্সটি সম্পূর্ণ খালি আঙুলের চামড়ার সীমানার ভেতরে সীমাবদ্ধ থাকে, তবে সিস্টেম নিশ্চিত হয় যে এটি খালি আঙুল এবং ডিটেকশনটি বাতিল করে। আর যদি আঙুলের মাথা থেকে বাস্তব কোনো অবজেক্ট অন্তত <b>২৫ পিক্সেল বাইরে প্রসারিত (protruded)</b> থাকে, তখনই কেবল এটি কনফার্ম করে যে ইউজার হাতে একটি আসল পেন ধরে আছে।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৫: FastAPI সার্ভারে একাধিক ক্লায়েন্ট ভিডিও দেখলে ল্যাগ করে না কেন?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, কারণ আমরা <b>Single-Pass JPEG Caching</b> করেছি। ভিডিও ফ্রেম প্রসেস ও বাউন্ডিং বক্স আঁকার কাজটি ব্যাকগ্রাউন্ডে একটি সিঙ্গেল এআই থ্রেডে একবারই হয় এবং মেমোরিতে <code>latest_jpeg_bytes</code> হিসেবে সেভ থাকে। ১০ জন ক্লায়েন্ট কানেক্ট হলেও সেই সেভ করা মেমোরি থেকে স্ট্রিম যায়, কাউকে নতুন করে এনকোড করতে হয় না। এতে CPU ব্যবহার ৭০% কমে যায়।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৬: প্রজেক্টে ক্লাউড বা টেলিগ্রাম বট ব্যবহার না করে লোকালি কেন করলে?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, ক্লাউড-বেজড ক্যামেরায় ভিডিও ফুটেজ থার্ড-পার্টি বিদেশি সার্ভারে যায় যা হ্যাক হতে পারে এবং প্রাইভেসি নষ্ট হয়। এছাড়া ইন্টারনেটে ফ্রেম পাঠাতে গেলে ২০০&ndash;৫০০ms লেটেন্সি তৈরি হয়। আমাদের Detecta সম্পূর্ণ <b>Local-First Architecture</b>&mdash;ইন্টারনেট ছাড়াও লোকাল ওয়াই-ফাইতে সাব-৫০ms লেটেন্সিতে শতভাগ নিরাপদে কাজ করে।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৭: সার্কিটে Pin 4 (GPIO 4)-এ রেজিস্টর ডিভাইডার কেন দেওয়া হয়েছে?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, ESP32-CAM এর অ্যানালগ পিন (ADC) সর্বোচ্চ ৩.৩ ভোল্ট পর্যন্ত সহ্য করতে পারে। কিন্তু আমাদের ব্যাটারি বা বুস্ট লাইনের ভোল্টেজ থাকে ৩.৭V থেকে ৫.০V পর্যন্ত। সরাসরি দিলে চিপের এডিসি পুড়ে যেত। তাই দুটি রেজিস্টর দিয়ে একটি ভোল্টেজ ডিভাইডার তৈরি করে ভোল্টেজকে ড্রপ করে ৩.৩V এর নিচে নামিয়ে পিন ৪ এ দেওয়া হয়েছে যাতে নিরাপদে ভোল্টেজ মনিটর করা যায়।&rdquo;</div>
    </div>

    <div class="qa-item">
      <div class="qa-q">প্রশ্ন ৮: YOLO11s এ কোন কোন ক্লাস ডিটেক্ট হয়? পার্সেল বা কার্টন বক্স কীভাবে চেনে?</div>
      <div class="qa-a"><b>উত্তর:</b> &ldquo;ম্যাম, আমরা ২১টি কিউরেটেড ক্লাস রেখেছি&mdash;মানুষ, ফোন, ল্যাপটপ, বোতল ইত্যাদি। আর বক্স ও পার্সেলের জন্য আমরা COCO ডেটাসেটের ক্লাস ২৪ ও ২৬ (Handbag/Box) এবং ক্লাস ২৮ (Suitcase/Carton/Box) কে ইন্টারনালি রি-ম্যাপ করে 'Box' হিসেবে কনফিগার করেছি। ফলে ডেলিভারি কার্টন এবং স্টোরেজ বক্স অনায়াসে ডিটেক্ট হয়।&rdquo;</div>
    </div>
  </div>

  <!-- SECTION 5: QUICK NUMBERS CHEAT SHEET -->
  <div class="section">
    <div class="section-title">৫. এক নজরে সব টেকনিক্যাল ডেটা ও সংখ্যা (Quick Numbers Cheat Sheet)</div>
    <table>
      <thead>
        <tr>
          <th>প্যারামিটার (Parameter)</th>
          <th>টেকনিক্যাল ভ্যালু / স্পেসিফিকেশন (Technical Specification)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>ক্যামেরা সেন্সর ও রেজোলিউশন</b></td>
          <td>OmniVision OV2640 (2.0 MP) | VGA (640 &times; 480), Quality = 16, 20MHz XCLK</td>
        </tr>
        <tr>
          <td><b>স্ট্রিমিং পোর্ট ও মেমোরি বাফার</b></td>
          <td>Dedicated HTTP Port 81 (<code>/stream</code>) | 4MB External PSRAM Dual-Buffer (<code>fb_count = 2</code>)</td>
        </tr>
        <tr>
          <td><b>লাইভ ফ্রেমরেট ও লেটেন্সি</b></td>
          <td><b>20.0 &ndash; 24.5 FPS</b> (Continuous over local Wi-Fi) | <b>~52 ms</b> End-to-End Latency</td>
        </tr>
        <tr>
          <td><b>অবজেক্ট ডিটেকশন মডেল</b></td>
          <td>Ultralytics YOLO11s (CUDA FP16 Tensor Cores) | <b>11.4 ms</b> Inference Latency</td>
        </tr>
        <tr>
          <td><b>টার্গেট অবজেক্ট ক্লাস সংখ্যা</b></td>
          <td>২১টি কিউরেটেড ক্লাস (মানুষ, বক্স/কার্টন, ল্যাপটপ, ফোন, কলম, বই, কিবোর্ড ইত্যাদি)</td>
        </tr>
        <tr>
          <td><b>ফেস রিকগনিশন মডেল</b></td>
          <td>InsightFace ArcFace (512-D Hyperspherical Vector, Cosine Similarity Threshold: 0.45)</td>
        </tr>
        <tr>
          <td><b>ফেস স্ট্রাইড ক্যাশিং ইনোভেশন</b></td>
          <td><b>২৫ ফ্রেম</b> স্ট্রাইড (Amortized Face Latency drops from 38ms to <b>&lt;2ms per frame</b>)</td>
        </tr>
        <tr>
          <td><b>হ্যান্ড জেসচার ও পেন ফিল্টার</b></td>
          <td>MediaPipe Hands (21 3D Landmarks, 7 Gestures) | Spatial Containment + 25px Protrusion</td>
        </tr>
        <tr>
          <td><b>সার্ভার ও ডেক্সটপ আর্কিটেকচার</b></td>
          <td>FastAPI (Single-Pass Cached Shared JPEG) | Microsoft Edge WebView2 (<code>Detecta.exe</code>)</td>
        </tr>
        <tr>
          <td><b>পাওয়ার ও ব্যাটারি ব্যাকআপ</b></td>
          <td>18650 Li-ion 3.7V (~12.21 Wh) | IP2312 3A Type-C Charger | XL6009 Boost 5.0V | <b>~৭.৫ ঘণ্টা ব্যাকআপ</b></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="footer-note">
    <strong>💡 শেষ কথা:</strong> প্রেজেন্টেশনের সময় শান্ত থাকবেন এবং সফটওয়্যার লিড হিসেবে আপনার তৈরি করা <strong>YOLO11s, ArcFace 25-Frame Stride Caching, এবং Smart Pen Algorithm</strong>-এর কথা আত্মবিশ্বাসের সাথে বলবেন। শুভকামনা!
  </div>

</body>
</html>
'''

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == "scripts" else script_dir
docs_assets_dir = os.path.join(root_dir, "docs", "assets")
os.makedirs(docs_assets_dir, exist_ok=True)

docs_html_path = os.path.join(docs_assets_dir, 'viva_script_compact.html')
with open(docs_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"Wrote {docs_html_path} successfully")

root_html_path = os.path.join(root_dir, 'viva_script_compact.html')
with open(root_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f"Wrote {root_html_path} successfully")
