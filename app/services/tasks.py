import asyncio
import os
import httpx
from uuid import UUID
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
    print(f"[TASK] Processing offer: {offer_id}")
    async def _process():
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

                # Iterate through matching requests and notify each passenger
                for match_request in matches:
                    passenger_tg = await service.telegram_user.find_by_user_id(match_request.passenger_id)
                    if not passenger_tg:
                        print(f"[TASK] No Telegram user found for passenger {match_request.passenger_id}")
                        continue
                    
                    passenger_chat_id = passenger_tg.chat_id if passenger_tg.chat_id else passenger_tg.telegram_id
                    
                    payload = {
                        "type": "new_offer_found",
                        "offer": offer_dto.model_dump(mode='json'),
                        "request_id": str(match_request.id),
                        "passenger_id": str(match_request.passenger_id),
                        "passenger_chat_id": passenger_chat_id,
                    }

                    async with httpx.AsyncClient() as client:
                        resp = await client.post(webhook_url, json=payload)
                        print(f"[TASK] Webhook sent for passenger {match_request.passenger_id}. Status: {resp.status_code}")
                    
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
    print(f"[TASK] Processing request: {request_id}")
    async def _process():
        service, session = await get_service()
        try:
            requests = await service.request_repo.get_by_id(UUID(request_id))
            if not requests:
                print(f"[TASK] Request not found: {request_id}")
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

                 payload = {
                    "type": "matches_found_for_request",
                    "request_id": request_id,
                    "passenger_id": str(req.passenger_id),
                    "passenger_telegram_id": passenger_telegram_id,
                    "passenger_chat_id": passenger_chat_id,
                    "matches": [m.model_dump(mode='json') for m in matches]
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
