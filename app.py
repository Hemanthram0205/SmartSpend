<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartSpend - Expense Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Inter', sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .metric-card {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
            border: 1px solid rgba(139, 92, 246, 0.2);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(139, 92, 246, 0.2);
            border-color: rgba(139, 92, 246, 0.4);
        }
        
        .nav-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover, .nav-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: transparent;
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .primary-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        
        .primary-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .danger-btn {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            transition: all 0.3s ease;
        }
        
        .danger-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(239, 68, 68, 0.4);
        }
        
        .input-field {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .input-field:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
            outline: none;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .table-row {
            transition: all 0.2s ease;
        }
        
        .table-row:hover {
            background: rgba(102, 126, 234, 0.1);
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .slide-in {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(102, 126, 234, 0.7);
        }
        
        .notification {
            animation: slideNotification 0.3s ease-out;
        }
        
        @keyframes slideNotification {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body class="text-white">
    <!-- Notification Container -->
    <div id="notification" class="fixed top-4 right-4 z-50 hidden"></div>

    <!-- Auth Page -->
    <div id="authPage" class="min-h-screen flex items-center justify-center p-4">
        <div class="w-full max-w-md">
            <div class="text-center mb-8 fade-in">
                <h1 class="text-5xl font-black gradient-text mb-2">SmartSpend</h1>
                <p class="text-gray-400">Track your expenses intelligently</p>
            </div>
            
            <!-- Login Form -->
            <div id="loginForm" class="glass-card rounded-2xl p-8 fade-in">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold">Welcome Back</h2>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Username</label>
                        <input type="text" id="loginUsername" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="Enter your username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Password</label>
                        <input type="password" id="loginPassword" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="Enter your password">
                    </div>
                    <button onclick="login()" class="primary-btn w-full py-3 rounded-xl font-semibold text-white mt-4">
                        Sign In
                    </button>
                </div>
                
                <div class="mt-6 text-center">
                    <p class="text-gray-400">Don't have an account? 
                        <button onclick="showRegister()" class="text-indigo-400 hover:text-indigo-300 font-medium">Create one</button>
                    </p>
                </div>
            </div>
            
            <!-- Register Form -->
            <div id="registerForm" class="glass-card rounded-2xl p-8 hidden fade-in">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
                        </svg>
                    </div>
                    <h2 class="text-2xl font-bold">Create Account</h2>
                </div>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Username</label>
                        <input type="text" id="regUsername" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="Choose a username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Email (optional)</label>
                        <input type="email" id="regEmail" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="your@email.com">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Password</label>
                        <input type="password" id="regPassword" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="Minimum 6 characters">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Confirm Password</label>
                        <input type="password" id="regConfirmPassword" class="input-field w-full px-4 py-3 rounded-xl text-white placeholder-gray-500" placeholder="Confirm your password">
                    </div>
                    <button onclick="register()" class="primary-btn w-full py-3 rounded-xl font-semibold text-white mt-4">
                        Create Account
                    </button>
                </div>
                
                <div class="mt-6 text-center">
                    <p class="text-gray-400">Already have an account? 
                        <button onclick="showLogin()" class="text-indigo-400 hover:text-indigo-300 font-medium">Sign in</button>
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main App -->
    <div id="mainApp" class="hidden min-h-screen">
        <!-- Header -->
        <header class="glass-card border-b border-white/10 sticky top-0 z-40">
            <div class="max-w-7xl mx-auto px-4 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <h1 class="text-2xl font-bold gradient-text">SmartSpend</h1>
                        <span class="hidden sm:inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-medium">
                            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                            </svg>
                            Private Space
                        </span>
                    </div>
                    <div class="flex items-center gap-4">
                        <div class="hidden sm:flex items-center gap-2 text-gray-300">
                            <div class="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-sm font-bold" id="userAvatar">U</div>
                            <span id="welcomeUser" class="font-medium">User</span>
                        </div>
                        <button onclick="logout()" class="danger-btn px-4 py-2 rounded-xl font-medium text-sm flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                            </svg>
                            <span class="hidden sm:inline">Logout</span>
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Navigation -->
        <nav class="max-w-7xl mx-auto px-4 py-6">
            <div class="flex flex-wrap justify-center gap-3">
                <button onclick="showPage('dashboard')" class="nav-btn active px-6 py-3 rounded-xl font-medium flex items-center gap-2" data-page="dashboard">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                    </svg>
                    Dashboard
                </button>
                <button onclick="showPage('add')" class="nav-btn px-6 py-3 rounded-xl font-medium flex items-center gap-2" data-page="add">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                    </svg>
                    Add Expense
                </button>
                <button onclick="showPage('view')" class="nav-btn px-6 py-3 rounded-xl font-medium flex items-center gap-2" data-page="view">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                    </svg>
                    View All
                </button>
                <button onclick="showPage('delete')" class="nav-btn px-6 py-3 rounded-xl font-medium flex items-center gap-2" data-page="delete">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                    Delete
                </button>
            </div>
        </nav>

        <!-- Content -->
        <main class="max-w-7xl mx-auto px-4 pb-12">
            <!-- Dashboard Page -->
            <div id="dashboardPage" class="fade-in">
                <!-- Metrics Grid -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Total Spent</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metricTotal">₹0.00</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">This Month</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metricMonth">₹0.00</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Transactions</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metricCount">0</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Daily Average</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metricAvg">₹0.00</p>
                    </div>
                </div>
                
                <!-- Second Row Metrics -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Last 7 Days</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metric7Days">₹0.00</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Last 30 Days</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metric30Days">₹0.00</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Avg Expense</span>
                        </div>
                        <p class="text-2xl font-bold text-white" id="metricAvgExpense">₹0.00</p>
                    </div>
                    
                    <div class="metric-card rounded-2xl p-5">
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-xl bg-teal-500/20 flex items-center justify-center">
                                <svg class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                                </svg>
                            </div>
                            <span class="text-gray-400 text-sm font-medium">Top Category</span>
                        </div>
                        <p class="text-xl font-bold text-white truncate" id="metricTopCat">N/A</p>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <div class="chart-container rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
                            </svg>
                            Monthly Trends
                        </h3>
                        <canvas id="monthlyChart" height="250"></canvas>
                    </div>
                    
                    <div class="chart-container rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/>
                            </svg>
                            Category Distribution
                        </h3>
                        <canvas id="categoryChart" height="250"></canvas>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="chart-container rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                            Daily Expenses (Last 30 Days)
                        </h3>
                        <canvas id="dailyChart" height="250"></canvas>
                    </div>
                    
                    <div class="chart-container rounded-2xl p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
                            </svg>
                            Expenses by Category
                        </h3>
                        <canvas id="categoryBarChart" height="250"></canvas>
                    </div>
                </div>
                
                <!-- Empty State -->
                <div id="emptyDashboard" class="hidden text-center py-16">
                    <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-indigo-500/20 flex items-center justify-center">
                        <svg class="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                        </svg>
                    </div>
                    <h3 class="text-2xl font-bold mb-2">No expenses yet</h3>
                    <p class="text-gray-400 mb-6">Start tracking your spending by adding your first expense</p>
                    <button onclick="showPage('add')" class="primary-btn px-6 py-3 rounded-xl font-semibold">
                        Add Your First Expense
                    </button>
                </div>
            </div>

            <!-- Add Expense Page -->
            <div id="addPage" class="hidden fade-in">
                <div class="max-w-2xl mx-auto">
                    <div class="glass-card rounded-2xl p-8">
                        <div class="flex items-center gap-3 mb-8">
                            <div class="w-12 h-12 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                                </svg>
                            </div>
                            <div>
                                <h2 class="text-2xl font-bold">Add New Expense</h2>
                                <p class="text-gray-400 text-sm">Track your spending</p>
                            </div>
                        </div>
                        
                        <form id="addExpenseForm" class="space-y-6">
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label class="block text-sm font-medium text-gray-300 mb-2">Category</label>
                                    <select id="expenseCategory" class="input-field w-full px-4 py-3 rounded-xl text-white" required>
                                        <option value="">Select category</option>
                                        <option value="Food">🍔 Food</option>
                                        <option value="Transport">🚗 Transport</option>
                                        <option value="Shopping">🛍️ Shopping</option>
                                        <option value="Bills">📄 Bills</option>
                                        <option value="Entertainment">🎬 Entertainment</option>
                                        <option value="Healthcare">🏥 Healthcare</option>
                                        <option value="Other">📦 Other</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-300 mb-2">Amount (₹)</label>
                                    <input type="number" id="expenseAmount" step="0.01" min="0.01" class="input-field w-full px-4 py-3 rounded-xl text-white" placeholder="0.00" required>
                                </div>
                            </div>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label class="block text-sm font-medium text-gray-300 mb-2">Date</label>
                                    <input type="date" id="expenseDate" class="input-field w-full px-4 py-3 rounded-xl text-white" required>
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-300 mb-2">Description (optional)</label>
                                    <input type="text" id="expenseDesc" class="input-field w-full px-4 py-3 rounded-xl text-white" placeholder="Enter description">
                                </div>
                            </div>
                            
                            <button type="submit" class="primary-btn w-full py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                                </svg>
                                Add Expense
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- View All Page -->
            <div id="viewPage" class="hidden fade-in">
                <div class="glass-card rounded-2xl overflow-hidden">
                    <div class="p-6 border-b border-white/10">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <div class="w-10 h-10 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center">
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                                    </svg>
                                </div>
                                <div>
                                    <h2 class="text-xl font-bold">All Expenses</h2>
                                    <p class="text-gray-400 text-sm" id="expenseCountText">0 expenses</p>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <input type="text" id="searchExpenses" class="input-field px-4 py-2 rounded-xl text-white text-sm" placeholder="Search...">
                            </div>
                        </div>
                    </div>
                    
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-white/5">
                                <tr>
                                    <th class="px-6 py-4 text-left text-sm font-semibold text-gray-300">Date</th>
                                    <th class="px-6 py-4 text-left text-sm font-semibold text-gray-300">Category</th>
                                    <th class="px-6 py-4 text-left text-sm font-semibold text-gray-300">Description</th>
                                    <th class="px-6 py-4 text-right text-sm font-semibold text-gray-300">Amount</th>
                                </tr>
                            </thead>
                            <tbody id="expenseTableBody" class="divide-y divide-white/5">
                                <!-- Expenses will be inserted here -->
                            </tbody>
                        </table>
                    </div>
                    
                    <div id="emptyViewState" class="hidden p-12 text-center">
                        <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                        </svg>
                        <p class="text-gray-400">No expenses found</p>
                    </div>
                </div>
            </div>

            <!-- Delete Page -->
            <div id="deletePage" class="hidden fade-in">
                <div class="max-w-2xl mx-auto">
                    <div class="glass-card rounded-2xl p-8">
                        <div class="flex items-center gap-3 mb-8">
                            <div class="w-12 h-12 rounded-xl bg-gradient-to-r from-red-500 to-rose-500 flex items-center justify-center">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </div>
                            <div>
                                <h2 class="text-2xl font-bold">Delete Expense</h2>
                                <p class="text-gray-400 text-sm">Remove unwanted entries</p>
                            </div>
                        </div>
                        
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-300 mb-2">Select expense to delete</label>
                            <select id="deleteSelect" class="input-field w-full px-4 py-3 rounded-xl text-white">
                                <option value="">Select an expense</option>
                            </select>
                        </div>
                        
                        <button onclick="deleteSelectedExpense()" class="danger-btn w-full py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            Delete Selected Expense
                        </button>
                        
                        <div id="emptyDeleteState" class="hidden text-center py-8">
                            <p class="text-gray-400">No expenses to delete</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // ========== DATA MANAGEMENT ==========
        const USERS_KEY = 'smartspend_users';
        const CURRENT_USER_KEY = 'smartspend_current_user';
        
        function getUsers() {
            return JSON.parse(localStorage.getItem(USERS_KEY) || '{}');
        }
        
        function saveUsers(users) {
            localStorage.setItem(USERS_KEY, JSON.stringify(users));
        }
        
        function getCurrentUser() {
            return localStorage.getItem(CURRENT_USER_KEY);
        }
        
        function setCurrentUser(username) {
            localStorage.setItem(CURRENT_USER_KEY, username);
        }
        
        function getExpenses() {
            const username = getCurrentUser();
            if (!username) return [];
            const users = getUsers();
            return users[username]?.expenses || [];
        }
        
        function saveExpenses(expenses) {
            const username = getCurrentUser();
            if (!username) return;
            const users = getUsers();
            if (!users[username]) users[username] = { expenses: [] };
            users[username].expenses = expenses;
            saveUsers(users);
        }
        
        // ========== AUTHENTICATION ==========
        function hashPassword(password) {
            let hash = 0;
            for (let i = 0; i < password.length; i++) {
                const char = password.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return hash.toString();
        }
        
        function showLogin() {
            document.getElementById('loginForm').classList.remove('hidden');
            document.getElementById('registerForm').classList.add('hidden');
        }
        
        function showRegister() {
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('registerForm').classList.remove('hidden');
        }
        
        function login() {
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !password) {
                showNotification('Please fill in all fields', 'error');
                return;
            }
            
            const users = getUsers();
            if (users[username] && users[username].password === hashPassword(password)) {
                setCurrentUser(username);
                showMainApp();
                showNotification('Welcome back, ' + username + '!', 'success');
            } else {
                showNotification('Invalid username or password', 'error');
            }
        }
        
        function register() {
            const username = document.getElementById('regUsername').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            const confirmPassword = document.getElementById('regConfirmPassword').value;
            
            if (!username || !password) {
                showNotification('Username and password are required', 'error');
                return;
            }
            
            if (password.length < 6) {
                showNotification('Password must be at least 6 characters', 'error');
                return;
            }
            
            if (password !== confirmPassword) {
                showNotification('Passwords do not match', 'error');
                return;
            }
            
            const users = getUsers();
            if (users[username]) {
                showNotification('Username already exists', 'error');
                return;
            }
            
            users[username] = {
                password: hashPassword(password),
                email: email,
                expenses: [],
                createdAt: new Date().toISOString()
            };
            
            saveUsers(users);
            showNotification('Account created! Please login.', 'success');
            showLogin();
            
            document.getElementById('regUsername').value = '';
            document.getElementById('regEmail').value = '';
            document.getElementById('regPassword').value = '';
            document.getElementById('regConfirmPassword').value = '';
        }
        
        function logout() {
            localStorage.removeItem(CURRENT_USER_KEY);
            document.getElementById('authPage').classList.remove('hidden');
            document.getElementById('mainApp').classList.add('hidden');
            document.getElementById('loginUsername').value = '';
            document.getElementById('loginPassword').value = '';
            showNotification('Logged out successfully', 'success');
        }
        
        function showMainApp() {
            const username = getCurrentUser();
            document.getElementById('authPage').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            document.getElementById('welcomeUser').textContent = username;
            document.getElementById('userAvatar').textContent = username.charAt(0).toUpperCase();
            
            // Set default date
            document.getElementById('expenseDate').valueAsDate = new Date();
            
            updateDashboard();
        }
        
        // ========== NOTIFICATIONS ==========
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            const bgColor = type === 'success' ? 'bg-emerald-500' : type === 'error' ? 'bg-red-500' : 'bg-indigo-500';
            
            notification.innerHTML = `
                <div class="notification ${bgColor} text-white px-6 py-4 rounded-xl shadow-lg flex items-center gap-3">
                    ${type === 'success' ? 
                        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' : 
                        type === 'error' ?
                        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>' :
                        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
                    }
                    <span class="font-medium">${message}</span>
                </div>
            `;
            
            notification.classList.remove('hidden');
            
            setTimeout(() => {
                notification.classList.add('hidden');
            }, 3000);
        }
        
        // ========== PAGE NAVIGATION ==========
        function showPage(page) {
            // Hide all pages
            document.getElementById('dashboardPage').classList.add('hidden');
            document.getElementById('addPage').classList.add('hidden');
            document.getElementById('viewPage').classList.add('hidden');
            document.getElementById('deletePage').classList.add('hidden');
            
            // Remove active from all nav buttons
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            
            // Show selected page
            document.getElementById(page + 'Page').classList.remove('hidden');
            document.querySelector(`[data-page="${page}"]`).classList.add('active');
            
            // Update content based on page
            if (page === 'dashboard') updateDashboard();
            if (page === 'view') updateExpenseTable();
            if (page === 'delete') updateDeleteSelect();
        }
        
        // ========== EXPENSE OPERATIONS ==========
        function addExpense(category, amount, date, description) {
            const expenses = getExpenses();
            const newExpense = {
                id: Date.now(),
                category,
                amount: parseFloat(amount),
                date,
                description: description || '',
                createdAt: new Date().toISOString()
            };
            expenses.push(newExpense);
            saveExpenses(expenses);
            return true;
        }
        
        function deleteExpense(id) {
            let expenses = getExpenses();
            expenses = expenses.filter(e => e.id !== id);
            saveExpenses(expenses);
            return true;
        }
        
        function deleteSelectedExpense() {
            const select = document.getElementById('deleteSelect');
            const id = parseInt(select.value);
            
            if (!id) {
                showNotification('Please select an expense to delete', 'error');
                return;
            }
            
            if (deleteExpense(id)) {
                showNotification('Expense deleted successfully!', 'success');
                updateDeleteSelect();
                updateDashboard();
            }
        }
        
        // ========== FORMAT HELPERS ==========
        function formatCurrency(amount) {
            return '₹' + amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        
        function formatDate(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        }
        
        function getCategoryEmoji(category) {
            const emojis = {
                'Food': '🍔',
                'Transport': '🚗',
                'Shopping': '🛍️',
                'Bills': '📄',
                'Entertainment': '🎬',
                'Healthcare': '🏥',
                'Other': '📦'
            };
            return emojis[category] || '📦';
        }
        
        // ========== DASHBOARD ==========
        let monthlyChart, categoryChart, dailyChart, categoryBarChart;
        
        function updateDashboard() {
            const expenses = getExpenses();
            
            if (expenses.length === 0) {
                document.getElementById('emptyDashboard').classList.remove('hidden');
                document.querySelectorAll('.metric-card, .chart-container').forEach(el => el.classList.add('hidden'));
                return;
            }
            
            document.getElementById('emptyDashboard').classList.add('hidden');
            document.querySelectorAll('.metric-card, .chart-container').forEach(el => el.classList.remove('hidden'));
            
            // Calculate metrics
            const now = new Date();
            const thisMonth = expenses.filter(e => {
                const d = new Date(e.date);
                return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
            });
            
            const last7Days = expenses.filter(e => {
                const d = new Date(e.date);
                const diff = (now - d) / (1000 * 60 * 60 * 24);
                return diff <= 7;
            });
            
            const last30Days = expenses.filter(e => {
                const d = new Date(e.date);
                const diff = (now - d) / (1000 * 60 * 60 * 24);
                return diff <= 30;
            });
            
            const total = expenses.reduce((sum, e) => sum + e.amount, 0);
            const monthTotal = thisMonth.reduce((sum, e) => sum + e.amount, 0);
            const last7Total = last7Days.reduce((sum, e) => sum + e.amount, 0);
            const last30Total = last30Days.reduce((sum, e) => sum + e.amount, 0);
            const avgExpense = total / expenses.length;
            const dailyAvg = last30Total / 30;
            
            // Find top category
            const categoryTotals = {};
            expenses.forEach(e => {
                categoryTotals[e.category] = (categoryTotals[e.category] || 0) + e.amount;
            });
            const topCategory = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';
            
            // Update metrics
            document.getElementById('metricTotal').textContent = formatCurrency(total);
            document.getElementById('metricMonth').textContent = formatCurrency(monthTotal);
            document.getElementById('metricCount').textContent = expenses.length;
            document.getElementById('metricAvg').textContent = formatCurrency(dailyAvg);
            document.getElementById('metric7Days').textContent = formatCurrency(last7Total);
            document.getElementById('metric30Days').textContent = formatCurrency(last30Total);
            document.getElementById('metricAvgExpense').textContent = formatCurrency(avgExpense);
            document.getElementById('metricTopCat').textContent = getCategoryEmoji(topCategory) + ' ' + topCategory;
            
            // Update charts
            updateCharts(expenses);
        }
        
        function updateCharts(expenses) {
            // Monthly trends
            const monthlyData = {};
            expenses.forEach(e => {
                const d = new Date(e.date);
                const key = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                monthlyData[key] = (monthlyData[key] || 0) + e.amount;
            });
            
            const monthLabels = Object.keys(monthlyData);
            const monthValues = Object.values(monthlyData);
            
            if (monthlyChart) monthlyChart.destroy();
            monthlyChart = new Chart(document.getElementById('monthlyChart'), {
                type: 'line',
                data: {
                    labels: monthLabels,
                    datasets: [{
                        label: 'Monthly Spending',
                        data: monthValues,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
            
            // Category pie chart
            const categoryData = {};
            expenses.forEach(e => {
                categoryData[e.category] = (categoryData[e.category] || 0) + e.amount;
            });
            
            if (categoryChart) categoryChart.destroy();
            categoryChart = new Chart(document.getElementById('categoryChart'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(categoryData),
                    datasets: [{
                        data: Object.values(categoryData),
                        backgroundColor: [
                            '#667eea', '#8b5cf6', '#ec4899', '#f43f5e', 
                            '#f97316', '#eab308', '#22c55e', '#14b8a6'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#9ca3af', padding: 20 }
                        }
                    },
                    cutout: '60%'
                }
            });
            
            // Daily expenses (last 30 days)
            const now = new Date();
            const dailyData = {};
            expenses.forEach(e => {
                const d = new Date(e.date);
                const diff = (now - d) / (1000 * 60 * 60 * 24);
                if (diff <= 30) {
                    const key = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    dailyData[key] = (dailyData[key] || 0) + e.amount;
                }
            });
            
            if (dailyChart) dailyChart.destroy();
            dailyChart = new Chart(document.getElementById('dailyChart'), {
                type: 'bar',
                data: {
                    labels: Object.keys(dailyData),
                    datasets: [{
                        label: 'Daily Spending',
                        data: Object.values(dailyData),
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af', maxRotation: 45 }
                        }
                    }
                }
            });
            
            // Category bar chart
            const sortedCategories = Object.entries(categoryData).sort((a, b) => b[1] - a[1]);
            
            if (categoryBarChart) categoryBarChart.destroy();
            categoryBarChart = new Chart(document.getElementById('categoryBarChart'), {
                type: 'bar',
                data: {
                    labels: sortedCategories.map(c => c[0]),
                    datasets: [{
                        label: 'Amount',
                        data: sortedCategories.map(c => c[1]),
                        backgroundColor: '#8b5cf6',
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#9ca3af' }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        }
        
        // ========== EXPENSE TABLE ==========
        function updateExpenseTable(filter = '') {
            const expenses = getExpenses();
            const tbody = document.getElementById('expenseTableBody');
            const emptyState = document.getElementById('emptyViewState');
            const countText = document.getElementById('expenseCountText');
            
            let filteredExpenses = expenses;
            if (filter) {
                const lowerFilter = filter.toLowerCase();
                filteredExpenses = expenses.filter(e => 
                    e.category.toLowerCase().includes(lowerFilter) ||
                    e.description.toLowerCase().includes(lowerFilter)
                );
            }
            
            // Sort by date descending
            filteredExpenses.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            countText.textContent = `${filteredExpenses.length} expense${filteredExpenses.length !== 1 ? 's' : ''}`;
            
            if (filteredExpenses.length === 0) {
                tbody.innerHTML = '';
                emptyState.classList.remove('hidden');
                return;
            }
            
            emptyState.classList.add('hidden');
            
            tbody.innerHTML = filteredExpenses.map(e => `
                <tr class="table-row">
                    <td class="px-6 py-4 text-sm text-gray-300">${formatDate(e.date)}</td>
                    <td class="px-6 py-4">
                        <span class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 text-sm">
                            ${getCategoryEmoji(e.category)} ${e.category}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-400">${e.description || '-'}</td>
                    <td class="px-6 py-4 text-sm font-semibold text-right text-emerald-400">${formatCurrency(e.amount)}</td>
                </tr>
            `).join('');
        }
        
        // ========== DELETE SELECT ==========
        function updateDeleteSelect() {
            const expenses = getExpenses();
            const select = document.getElementById('deleteSelect');
            const emptyState = document.getElementById('emptyDeleteState');
            
            // Sort by date descending
            expenses.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            if (expenses.length === 0) {
                select.classList.add('hidden');
                document.querySelector('#deletePage button').classList.add('hidden');
                emptyState.classList.remove('hidden');
                return;
            }
            
            select.classList.remove('hidden');
            document.querySelector('#deletePage button').classList.remove('hidden');
            emptyState.classList.add('hidden');
            
            select.innerHTML = '<option value="">Select an expense</option>' + 
                expenses.map(e => `
                    <option value="${e.id}">
                        ${formatDate(e.date)} - ${getCategoryEmoji(e.category)} ${e.category} - ${formatCurrency(e.amount)}${e.description ? ' - ' + e.description : ''}
                    </option>
                `).join('');
        }
        
        // ========== EVENT LISTENERS ==========
        document.getElementById('addExpenseForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const category = document.getElementById('expenseCategory').value;
            const amount = document.getElementById('expenseAmount').value;
            const date = document.getElementById('expenseDate').value;
            const description = document.getElementById('expenseDesc').value;
            
            if (!category || !amount || !date) {
                showNotification('Please fill in all required fields', 'error');
                return;
            }
            
            if (addExpense(category, amount, date, description)) {
                showNotification('Expense added successfully!', 'success');
                this.reset();
                document.getElementById('expenseDate').valueAsDate = new Date();
                updateDashboard();
            }
        });
        
        document.getElementById('searchExpenses').addEventListener('input', function(e) {
            updateExpenseTable(e.target.value);
        });
        
        // Login on Enter key
        document.getElementById('loginPassword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') login();
        });
        
        document.getElementById('regConfirmPassword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') register();
        });
        
        // ========== INITIALIZATION ==========
        document.addEventListener('DOMContentLoaded', function() {
            const currentUser = getCurrentUser();
            if (currentUser) {
                showMainApp();
            }
        });
    </script>
</body>
</html>
