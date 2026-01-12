import asyncio
import os
import httpx
from uuid import UUID
from sqlalchemy import select
from app.core.celery_app import celery_app
# from app.infrastructure.connections.database import get_session_context # This doesn't exist
# We need the session maker
from app.infrastructure.connections.database.session import async_session_maker
from app.services.ride_service import RideService
from app.infrastructure.repositories.ride import (
    RideOfferRepository, RideRequestRepository, CarPhotoRepository
)
from app.domain.interfaces.media_service import IMediaService

# Mock Media Service for Worker (or use real one if env var present)
class MockMediaService(IMediaService):
    async def upload_file(self, public_id: str, file: bytes) -> dict:
        return {"url": "http://mock"}
    async def get_file_url(self, public_id: str) -> str:
        return "http://mock"

async def get_service():
    """Helper to get service with new session"""
    # Create session directly from maker
    session = async_session_maker()
    
    offer_repo = RideOfferRepository(session)
    request_repo = RideRequestRepository(session)
    photo_repo = CarPhotoRepository(session)
    # We need Telegram User Repo to find Telegram ID
    from app.infrastructure.repositories.user import TelegramUserRepository
    telegram_user_repo = TelegramUserRepository(session)
    
    media_service = MockMediaService() 
    
    # RideService needs to be updated to accept telegram_user_repo if we use it there? 
    # Or we can just attach it to the service object dynamically for this script or use it directly.
    # RideService constructor signature: (session, offer_repo, request_repo, photo_repo, media_service)
    # It does NOT take telegram_user_repo.
    
    service = RideService(session, offer_repo, request_repo, photo_repo, media_service)
    service.telegram_user = telegram_user_repo # Monkey patch for local access in this script logic
    
    return service, session
    
    return RideService(session, offer_repo, request_repo, photo_repo, media_service), session

def run_async(coro):
    """Helper to run async code in sync celery task"""
    loop = asyncio.get_event_loop()
    if loop.is_running():
         # Should not happen in worker process standard setup
         return loop.create_task(coro)
    else:
         return loop.run_until_complete(coro)

@celery_app.task
def process_ride_offer(offer_id: str):
    """
    Search for requests matching this offer and notify bot.
    """
    with open("/app/celery_debug.log", "a") as f:
        f.write(f"[TASK] Processing offer START: {offer_id}\n")
    
    print(f"[TASK] Processing offer: {offer_id}")
    async def _process():
        with open("/app/celery_debug.log", "a") as f:
            f.write(f"[TASK] Inside _process for offer: {offer_id}\n")
        service, session = await get_service()
        try:
            offer = await service.offer_repo.get_by_id(UUID(offer_id))
            if not offer:
                print(f"[TASK] Offer not found: {offer_id}")
                return

            print(f"[TASK] Offer found. Driver ID: {offer.driver_id}")
            
            # Get Driver Telegram ID
            driver_tg = await service.telegram_user.find_by_user_id(offer.driver_id)
            driver_telegram_id = driver_tg.telegram_id if driver_tg else None
            driver_chat_id = driver_tg.chat_id if driver_tg and driver_tg.chat_id else driver_telegram_id
            print(f"[TASK] Driver Telegram ID: {driver_telegram_id}, Chat ID: {driver_chat_id}")

            # Search Requests
            from app.representations.dtos.ride import RideRequestSearchDTO
            dt = RideRequestSearchDTO(
                start_location=offer.start_location,
                end_location=offer.end_location,
                start_time=offer.travel_start_date,
                limit=10,
                offset=0
            )
            print(f"[TASK] Searching requests with: {dt}")
            matches = await service.search_ride_requests(dt)
            print(f"[TASK] Found {len(matches)} matches")
            
            if matches:
                webhook_url = os.getenv("BOT_WEBHOOK_URL")
                print(f"[TASK] Webhook URL: {webhook_url}")
                
                if not webhook_url: return

                from app.representations.dtos.ride import RideOfferDTO
                offer_dto = RideOfferDTO.model_validate(offer)

                # Get Driver Info for Notification
                # Fetch User for phone number
                from app.domain.models.user import User
                user_stmt = select(User).where(User.id == offer.driver_id)
                user_result = await session.execute(user_stmt)
                driver_user_model = user_result.scalars().first()
                driver_phone = driver_user_model.phone_number if driver_user_model else None

                driver_username = driver_tg.username if driver_tg else None
                
                # Fetch Car Photos
                photos = await service.photo_repo.get_by_driver(offer.driver_id)
                photo_urls = [p.url for p in photos]

                # Iterate through matching requests and notify each passenger
                # 1. Collect all passenger IDs
                passenger_ids = [m.passenger_id for m in matches]
                print(f"[TASK] Found {len(matches)} matching requests. Passenger IDs: {passenger_ids}")
                with open("/app/celery_debug.log", "a") as f:
                    f.write(f"[TASK] Found matches: {len(matches)}\n")
                
                # 2. Batch fetch passenger telegram users
                from app.domain.models.user import TelegramUser
                
                stmt = select(TelegramUser).where(TelegramUser.user_id.in_(passenger_ids))
                result = await session.execute(stmt)
                telegram_users = result.scalars().all()
                print(f"[TASK] Fetched {len(telegram_users)} Telegram users for passengers")
                
                # Map passenger_id to chat_id
                passenger_map = {}
                for tu in telegram_users:
                     chat_id = tu.chat_id if tu.chat_id else tu.telegram_id
                     passenger_map[tu.user_id] = chat_id
                
                print(f"[TASK] Passenger Map: {passenger_map}")

                async with httpx.AsyncClient() as client:
                    tasks = []
                    for match_request in matches:
                        p_id = match_request.passenger_id
                        passenger_chat_id = passenger_map.get(p_id)
                        
                        if not passenger_chat_id:
                            print(f"[TASK] No Telegram user found for passenger {p_id}")
                            with open("/app/celery_debug.log", "a") as f:
                                f.write(f"[TASK] No TG User for {p_id}\n")
                            continue

                        payload = {
                            "type": "new_offer_found",
                            "offer": {
                                **offer_dto.model_dump(mode='json'),
                                "driver_phone": driver_phone,
                                "driver_username": driver_username,
                                "car_photos": photo_urls
                            },
                            "request_id": str(match_request.id),
                            "passenger_id": str(match_request.passenger_id),
                            "passenger_chat_id": passenger_chat_id,
                        }
                        
                        logger_msg = f"Sending webhook to {passenger_chat_id} for request {match_request.id}"
                        print(f"[TASK] {logger_msg}")
                        tasks.append(client.post(webhook_url, json=payload))
                    
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for i, res in enumerate(results):
                             if isinstance(res, Exception):
                                 print(f"[TASK] Webhook error: {res}")
                             else:
                                 print(f"[TASK] Webhook sent. Status: {res.status_code}")
                    
        except Exception as e:
            print(f"[TASK] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()

    import asyncio
    try:
        asyncio.run(_process())
    except RuntimeError:
        # Fallback if a loop is already running (e.g. in some nested context)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_process())

@celery_app.task
def process_ride_request(request_id: str):
    """
    Search for offers matching this request and notify bot.
    """
    with open("/app/celery_debug.log", "a") as f:
        f.write(f"[TASK] Processing request START: {request_id}\n")

    print(f"[TASK] Processing request: {request_id}")
    async def _process():
        service, session = await get_service()
        try:
            with open("/app/celery_debug.log", "a") as f:
                f.write(f"[TASK] Inside _process for request: {request_id}\n")

            requests = await service.request_repo.get_by_id(UUID(request_id))
            if not requests:
                print(f"[TASK] Request not found: {request_id}")
                with open("/app/celery_debug.log", "a") as f:
                    f.write(f"[TASK] Request not found: {request_id}\n")
                return
            req = requests
            
            print(f"[TASK] Request found. Passenger ID: {req.passenger_id}")

            # Get Passenger Telegram ID
            passenger_tg = await service.telegram_user.find_by_user_id(req.passenger_id)
            passenger_telegram_id = passenger_tg.telegram_id if passenger_tg else None
            passenger_chat_id = passenger_tg.chat_id if passenger_tg and passenger_tg.chat_id else passenger_telegram_id
            print(f"[TASK] Passenger Telegram ID: {passenger_telegram_id}, Chat ID: {passenger_chat_id}")

            # Search Offers
            from app.representations.dtos.ride import RideOfferSearchDTO
            seats = 1
            if req.seat_amount and req.seat_amount.isdigit():
                seats = int(req.seat_amount)
            
            dt = RideOfferSearchDTO(
                start_location=req.start_location,
                end_location=req.end_location,
                seats_needed=seats,
                start_time=req.travel_start_date,
                limit=10
            )
            print(f"[TASK] Searching offers with: {dt}")
            matches = await service.search_ride_offers(dt)
            print(f"[TASK] Found {len(matches)} matches")
            
            if matches:
                 webhook_url = os.getenv("BOT_WEBHOOK_URL")
                 print(f"[TASK] Webhook URL: {webhook_url}")
                 if not webhook_url: return

                 # Enrich matches with driver info in BATCH
                 enriched_matches = []
                 from app.domain.models.user import User, TelegramUser
                 from app.domain.models.ride import CarPhoto

                 if matches:
                     driver_ids = list(set([m.driver_id for m in matches]))
                     
                     # 1. Fetch Users (Phones)
                     user_stmt = select(User).where(User.id.in_(driver_ids))
                     user_res = await session.execute(user_stmt)
                     users_map = {u.id: u for u in user_res.scalars().all()}
                     
                     # 2. Fetch Telegram Users (Usernames)
                     tg_stmt = select(TelegramUser).where(TelegramUser.user_id.in_(driver_ids))
                     tg_res = await session.execute(tg_stmt)
                     tg_map = {t.user_id: t for t in tg_res.scalars().all()}
                     
                     # 3. Fetch Photos
                     # Need a way to fetch photos for multiple drivers.
                     # Assuming CarPhoto model has driver_id
                     photo_stmt = select(CarPhoto).where(CarPhoto.driver_id.in_(driver_ids))
                     photo_res = await session.execute(photo_stmt)
                     photos_list = photo_res.scalars().all()
                     
                     # Group photos by driver_id
                     photos_map = {}
                     for p in photos_list:
                         if p.driver_id not in photos_map:
                             photos_map[p.driver_id] = []
                         photos_map[p.driver_id].append(p.url)

                     for m in matches:
                         d_id = m.driver_id
                         
                         driver_user_model = users_map.get(d_id)
                         driver_phone = driver_user_model.phone_number if driver_user_model else None
                         
                         driver_tg = tg_map.get(d_id)
                         driver_username = driver_tg.username if driver_tg else None
                         
                         photo_urls = photos_map.get(d_id, [])
                         
                         enriched_match = {
                             **m.model_dump(mode='json'),
                             "driver_phone": driver_phone,
                             "driver_username": driver_username,
                             "car_photos": photo_urls
                         }
                         enriched_matches.append(enriched_match)

                 payload = {
                    "type": "matches_found_for_request",
                    "request_id": request_id,
                    "passenger_id": str(req.passenger_id),
                    "passenger_telegram_id": passenger_telegram_id,
                    "passenger_chat_id": passenger_chat_id,
                    "matches": enriched_matches
                 }
                 async with httpx.AsyncClient() as client:
                    resp = await client.post(webhook_url, json=payload)
                    print(f"[TASK] Webhook sent. Status: {resp.status_code}")
        except Exception as e:
            print(f"[TASK] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()

    import asyncio
    try:
        asyncio.run(_process())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_process())
