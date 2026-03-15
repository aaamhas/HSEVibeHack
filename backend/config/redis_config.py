import os
import redis.asyncio as redis
from typing import Optional

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REFRESH_TOKEN_TTL = 7 * 24 * 60 * 60  # 7 days in seconds
REFRESH_TOKEN_PREFIX = "refresh_token"
ACCESS_TOKEN_PREFIX = "access_token"

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client (singleton pattern)"""
    global _redis_client

    if _redis_client is None:
        _redis_client = await redis.from_url(
            REDIS_URL,
            encoding="utf8",
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Test connection
        try:
            await _redis_client.ping()
            print("✓ Redis connected successfully")
        except redis.ConnectionError as e:
            print(f"✗ Redis connection failed: {e}")
            raise

    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        print("✓ Redis connection closed")


async def store_refresh_token(user_id: int, token_uuid: str, token_data: str) -> None:
    """
    Store refresh token in Redis with TTL

    Args:
        user_id: User ID
        token_uuid: UUID for this specific token
        token_data: Token data to store
    """
    client = await get_redis_client()
    key = f"{REFRESH_TOKEN_PREFIX}:{user_id}:{token_uuid}"
    await client.setex(key, REFRESH_TOKEN_TTL, token_data)


async def get_refresh_token(user_id: int, token_uuid: str) -> Optional[str]:
    """
    Retrieve refresh token from Redis

    Returns:
        Token data if found and valid, None otherwise
    """
    client = await get_redis_client()
    key = f"{REFRESH_TOKEN_PREFIX}:{user_id}:{token_uuid}"
    return await client.get(key)


async def delete_refresh_token(user_id: int, token_uuid: str) -> bool:
    """
    Delete refresh token from Redis (logout)

    Returns:
        True if token was deleted, False if it didn't exist
    """
    client = await get_redis_client()
    key = f"{REFRESH_TOKEN_PREFIX}:{user_id}:{token_uuid}"
    result = await client.delete(key)
    return result > 0


async def clear_all_user_tokens(user_id: int) -> int:
    """
    Clear all refresh tokens for a user (e.g., when resetting password)

    Returns:
        Number of tokens deleted
    """
    client = await get_redis_client()
    pattern = f"{REFRESH_TOKEN_PREFIX}:{user_id}:*"
    keys = await client.keys(pattern)

    if keys:
        return await client.delete(*keys)
    return 0


async def get_user_token_count(user_id: int) -> int:
    """Get number of active refresh tokens for a user"""
    client = await get_redis_client()
    pattern = f"{REFRESH_TOKEN_PREFIX}:{user_id}:*"
    keys = await client.keys(pattern)
    return len(keys)
