import instaloader
import json
import google.generativeai as genai
import time
import random
import requests
from datetime import datetime
import os
import logging

# Configuration
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel(
    'models/gemini-1.5-pro-002',
    tools={'google_search_retrieval': {}},
    system_instruction="You are a professional social media analyst."
)

# Anti-blocking setup
MOBILE_HEADERS = {
    "X-IG-App-ID": "238260118172367",
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Referer": "https://www.instagram.com/",
    "X-Requested-With": "XMLHttpRequest"
}

def safe_json_parse(text):
    """Robust JSON parsing with error recovery"""
    clean_text = text.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        try:
            start = max(clean_text.find('{'), clean_text.find('['))
            end = max(clean_text.rfind('}'), clean_text.rfind(']')) + 1
            return json.loads(clean_text[start:end])
        except:
            return {"error": "JSON parsing failed", "raw_response": clean_text[:200]}

def get_instagram_data(username):
    """Instagram scraper with IP rotation prevention"""
    try:
        # Random mobile user agents
        user_agent = random.choice([
            "Mozilla/5.0 (Linux; Android 12; SM-S906N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.6422.168 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/15.0 Mobile/19A346 Safari/602.1"
        ])
        
        L = instaloader.Instaloader(
            user_agent=user_agent,
            sleep=True,
            quiet=True,
            request_timeout=120,
            max_connection_attempts=2
        )
        
        # Fresh session with Tor proxy
        L.context._session = requests.Session()
        L.context._session.proxies = {
            'http': 'socks5://localhost:9050',
            'https': 'socks5://localhost:9050'
        }
        
        # Dynamic headers
        headers = MOBILE_HEADERS.copy()
        headers.update({
            "X-IG-Device-ID": f"android-{''.join(random.choices('abcdef0123456789', k=16))}",
            "User-Agent": user_agent
        })
        L.context._session.headers.update(headers)
        
        # Human-like delay
        time.sleep(random.uniform(3.5, 7.8))
        
        profile = instaloader.Profile.from_username(L.context, username)
        
        if profile.is_private:
            return {"error": f"Private profile @{username}"}

        # Random post collection (1-3 posts)
        posts = []
        for i, post in enumerate(profile.get_posts()):
            if i >= random.randint(1, 3):
                break
            posts.append({
                "id": post.shortcode,
                "likes": post.likes,
                "comments": post.comments,
                "caption": post.caption,
                "type": "video" if post.is_video else "image",
                "timestamp": post.date_utc.isoformat()
            })
            time.sleep(random.uniform(2.8, 5.4))
        
        return {
            "username": profile.username,
            "full_name": profile.full_name,
            "bio": profile.biography,
            "followers": profile.followers,
            "following": profile.followees,
            "posts_count": profile.mediacount,
            "profile_pic": profile.profile_pic_url,
            "is_verified": profile.is_verified,
            "recent_posts": posts,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except instaloader.exceptions.QueryReturnedBadRequestException:
        return {"error": "Instagram API blocked - wait 24 hours"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def generate_company_report(instagram_data):
    """Generate company profile from Instagram data"""
    try:
        analysis_prompt = f"""
        Analyze this social media profile to create detailed company report:
        {json.dumps(instagram_data, indent=2)}
        
        Include in JSON format:
        - company_name
        - industry
        - core_offerings (list)
        - target_demographics
        - unique_value_proposition
        - brand_voice
        - estimated_team_size
        - geographic_operation
        - content_strategy_analysis
        """
        response = model.generate_content(analysis_prompt)
        return safe_json_parse(response.text)
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def find_competitors(company_report):
    """Find competitors using Google-grounded search"""
    try:
        prompt = f"""
        Based on this company profile, identify top competitors with Instagram handles.
        Use Google Search grounding for accuracy. Return JSON format:
        {{
            "competitors": [
                {{
                    "name": "",
                    "industry_match": "",
                    "instagram": "",
                    "competition_level": "high/medium/low",
                    "reason": ""
                }}
            ]
        }}
        
        Company Profile:
        {json.dumps(company_report, indent=2)}
        """
        response = model.generate_content(prompt)
        return safe_json_parse(response.text).get("competitors", [])
    except Exception as e:
        return []

def analyze_performance(data):
    """Generate performance insights"""
    try:
        prompt = f"""
        Analyze social media performance metrics and generate insights:
        {json.dumps(data, indent=2)}
        
        Include in JSON:
        - engagement_rate
        - optimal_posting_times
        - content_type_breakdown
        - hashtag_performance
        - growth_strategy
        - improvement_recommendations
        """
        response = model.generate_content(prompt)
        return safe_json_parse(response.text)
    except Exception as e:
        return {"error": f"Performance analysis failed: {str(e)}"}

def analyze_account(target_account):
    """Main analysis workflow"""
    start_time = time.time()
    
    max_retries = 2
    company_data = {}
    for attempt in range(max_retries):
        logging.info(f"Attempt {attempt+1}/{max_retries} to collect data...")
        company_data = get_instagram_data(target_account)
        if "error" not in company_data:
            break
        wait_time = 2 ** (attempt + 1) + random.uniform(0, 2)
        logging.info(f"Waiting {wait_time:.1f} seconds before retry...")
        time.sleep(wait_time)
    
    if "error" in company_data:
        return {"error": company_data['error'], "execution_time": time.time() - start_time}
    
    company_report = generate_company_report(company_data)
    competitors = find_competitors(company_report)
    
    competitor_analysis = []
    for comp in competitors[:2]:
        if comp.get('instagram'):
            handle = comp['instagram'].lstrip('@')
            logging.info(f"Analyzing competitor: {handle}")
            comp_data = get_instagram_data(handle)
            if "error" not in comp_data:
                analysis = analyze_performance(comp_data)
                competitor_analysis.append({
                    "competitor_info": comp,
                    "data": comp_data,
                    "analysis": analysis
                })
            time.sleep(random.uniform(3, 6))
    
    return {
        "target_analysis": analyze_performance(company_data),
        "company_profile": company_report,
        "competitor_insights": competitor_analysis,
        "generated_at": datetime.utcnow().isoformat(),
        "execution_time": time.time() - start_time
    }
