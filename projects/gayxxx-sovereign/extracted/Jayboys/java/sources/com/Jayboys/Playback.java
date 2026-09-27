package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00002\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0019\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001BS\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0003\u0012\u0006\u0010\u0005\u001a\u00020\u0003\u0012\u000e\b\u0001\u0010\u0006\u001a\b\u0012\u0004\u0012\u00020\u00030\u0007\u0012\b\b\u0001\u0010\b\u001a\u00020\u0003\u0012\b\b\u0001\u0010\t\u001a\u00020\n\u0012\u0006\u0010\u000b\u001a\u00020\u0003\u0012\u0006\u0010\f\u001a\u00020\u0003¢\u0006\u0004\b\r\u0010\u000eJ\t\u0010\u001a\u001a\u00020\u0003HÆ\u0003J\t\u0010\u001b\u001a\u00020\u0003HÆ\u0003J\t\u0010\u001c\u001a\u00020\u0003HÆ\u0003J\u000f\u0010\u001d\u001a\b\u0012\u0004\u0012\u00020\u00030\u0007HÆ\u0003J\t\u0010\u001e\u001a\u00020\u0003HÆ\u0003J\t\u0010\u001f\u001a\u00020\nHÆ\u0003J\t\u0010 \u001a\u00020\u0003HÆ\u0003J\t\u0010!\u001a\u00020\u0003HÆ\u0003J_\u0010\"\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u00032\b\b\u0002\u0010\u0004\u001a\u00020\u00032\b\b\u0002\u0010\u0005\u001a\u00020\u00032\u000e\b\u0003\u0010\u0006\u001a\b\u0012\u0004\u0012\u00020\u00030\u00072\b\b\u0003\u0010\b\u001a\u00020\u00032\b\b\u0003\u0010\t\u001a\u00020\n2\b\b\u0002\u0010\u000b\u001a\u00020\u00032\b\b\u0002\u0010\f\u001a\u00020\u0003HÆ\u0001J\u0014\u0010#\u001a\u00020$2\b\u0010%\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010&\u001a\u00020'HÖ\u0081\u0004J\n\u0010(\u001a\u00020\u0003HÖ\u0081\u0004R\u0011\u0010\u0002\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u0011\u0010\u0004\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0011\u0010\u0010R\u0011\u0010\u0005\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0012\u0010\u0010R\u001c\u0010\u0006\u001a\b\u0012\u0004\u0012\u00020\u00030\u00078\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0013\u0010\u0014R\u0016\u0010\b\u001a\u00020\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0016\u0010\t\u001a\u00020\n8\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0016\u0010\u0017R\u0011\u0010\u000b\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0018\u0010\u0010R\u0011\u0010\f\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0010¨\u0006)"}, d2 = {"Lcom/Jayboys/Playback;", "", "algorithm", "", "iv", "payload", "keyParts", "", "expiresAt", "decryptKeys", "Lcom/Jayboys/DecryptKeys;", "iv2", "payload2", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/util/List;Ljava/lang/String;Lcom/Jayboys/DecryptKeys;Ljava/lang/String;Ljava/lang/String;)V", "getAlgorithm", "()Ljava/lang/String;", "getIv", "getPayload", "getKeyParts", "()Ljava/util/List;", "getExpiresAt", "getDecryptKeys", "()Lcom/Jayboys/DecryptKeys;", "getIv2", "getPayload2", "component1", "component2", "component3", "component4", "component5", "component6", "component7", "component8", "copy", "equals", "", "other", "hashCode", "", "toString", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class Playback {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String algorithm;

    @com.fasterxml.jackson.annotation.JsonProperty("decrypt_keys")
    @org.jetbrains.annotations.NotNull
    private final com.Jayboys.DecryptKeys decryptKeys;

    @com.fasterxml.jackson.annotation.JsonProperty("expires_at")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String expiresAt;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String iv;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String iv2;

    @com.fasterxml.jackson.annotation.JsonProperty("key_parts")
    @org.jetbrains.annotations.NotNull
    private final java.util.List<java.lang.String> keyParts;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String payload;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String payload2;

    /* JADX WARN: Multi-variable type inference failed */
    public static /* synthetic */ com.Jayboys.Playback copy$default(com.Jayboys.Playback playback, java.lang.String str, java.lang.String str2, java.lang.String str3, java.util.List list, java.lang.String str4, com.Jayboys.DecryptKeys decryptKeys, java.lang.String str5, java.lang.String str6, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = playback.algorithm;
        }
        if ((i & 2) != 0) {
            str2 = playback.iv;
        }
        if ((i & 4) != 0) {
            str3 = playback.payload;
        }
        if ((i & 8) != 0) {
            list = playback.keyParts;
        }
        if ((i & 16) != 0) {
            str4 = playback.expiresAt;
        }
        if ((i & 32) != 0) {
            decryptKeys = playback.decryptKeys;
        }
        if ((i & 64) != 0) {
            str5 = playback.iv2;
        }
        if ((i & 128) != 0) {
            str6 = playback.payload2;
        }
        java.lang.String str7 = str5;
        java.lang.String str8 = str6;
        java.lang.String str9 = str4;
        com.Jayboys.DecryptKeys decryptKeys2 = decryptKeys;
        return playback.copy(str, str2, str3, list, str9, decryptKeys2, str7, str8);
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getAlgorithm() {
        return this.algorithm;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getIv() {
        return this.iv;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getPayload() {
        return this.payload;
    }

    @org.jetbrains.annotations.NotNull
    public final java.util.List<java.lang.String> component4() {
        return this.keyParts;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component5, reason: from getter */
    public final java.lang.String getExpiresAt() {
        return this.expiresAt;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component6, reason: from getter */
    public final com.Jayboys.DecryptKeys getDecryptKeys() {
        return this.decryptKeys;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component7, reason: from getter */
    public final java.lang.String getIv2() {
        return this.iv2;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component8, reason: from getter */
    public final java.lang.String getPayload2() {
        return this.payload2;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.Playback copy(@org.jetbrains.annotations.NotNull java.lang.String algorithm, @org.jetbrains.annotations.NotNull java.lang.String iv, @org.jetbrains.annotations.NotNull java.lang.String payload, @com.fasterxml.jackson.annotation.JsonProperty("key_parts") @org.jetbrains.annotations.NotNull java.util.List<java.lang.String> keyParts, @com.fasterxml.jackson.annotation.JsonProperty("expires_at") @org.jetbrains.annotations.NotNull java.lang.String expiresAt, @com.fasterxml.jackson.annotation.JsonProperty("decrypt_keys") @org.jetbrains.annotations.NotNull com.Jayboys.DecryptKeys decryptKeys, @org.jetbrains.annotations.NotNull java.lang.String iv2, @org.jetbrains.annotations.NotNull java.lang.String payload2) {
        return new com.Jayboys.Playback(algorithm, iv, payload, keyParts, expiresAt, decryptKeys, iv2, payload2);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Jayboys.Playback)) {
            return false;
        }
        com.Jayboys.Playback playback = (com.Jayboys.Playback) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.algorithm, playback.algorithm) && kotlin.jvm.internal.Intrinsics.areEqual(this.iv, playback.iv) && kotlin.jvm.internal.Intrinsics.areEqual(this.payload, playback.payload) && kotlin.jvm.internal.Intrinsics.areEqual(this.keyParts, playback.keyParts) && kotlin.jvm.internal.Intrinsics.areEqual(this.expiresAt, playback.expiresAt) && kotlin.jvm.internal.Intrinsics.areEqual(this.decryptKeys, playback.decryptKeys) && kotlin.jvm.internal.Intrinsics.areEqual(this.iv2, playback.iv2) && kotlin.jvm.internal.Intrinsics.areEqual(this.payload2, playback.payload2);
    }

    public int hashCode() {
        return (((((((((((((this.algorithm.hashCode() * 31) + this.iv.hashCode()) * 31) + this.payload.hashCode()) * 31) + this.keyParts.hashCode()) * 31) + this.expiresAt.hashCode()) * 31) + this.decryptKeys.hashCode()) * 31) + this.iv2.hashCode()) * 31) + this.payload2.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "Playback(algorithm=" + this.algorithm + ", iv=" + this.iv + ", payload=" + this.payload + ", keyParts=" + this.keyParts + ", expiresAt=" + this.expiresAt + ", decryptKeys=" + this.decryptKeys + ", iv2=" + this.iv2 + ", payload2=" + this.payload2 + ')';
    }

    public Playback(@org.jetbrains.annotations.NotNull java.lang.String algorithm, @org.jetbrains.annotations.NotNull java.lang.String iv, @org.jetbrains.annotations.NotNull java.lang.String payload, @com.fasterxml.jackson.annotation.JsonProperty("key_parts") @org.jetbrains.annotations.NotNull java.util.List<java.lang.String> list, @com.fasterxml.jackson.annotation.JsonProperty("expires_at") @org.jetbrains.annotations.NotNull java.lang.String expiresAt, @com.fasterxml.jackson.annotation.JsonProperty("decrypt_keys") @org.jetbrains.annotations.NotNull com.Jayboys.DecryptKeys decryptKeys, @org.jetbrains.annotations.NotNull java.lang.String iv2, @org.jetbrains.annotations.NotNull java.lang.String payload2) {
        this.algorithm = algorithm;
        this.iv = iv;
        this.payload = payload;
        this.keyParts = list;
        this.expiresAt = expiresAt;
        this.decryptKeys = decryptKeys;
        this.iv2 = iv2;
        this.payload2 = payload2;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getAlgorithm() {
        return this.algorithm;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getIv() {
        return this.iv;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getPayload() {
        return this.payload;
    }

    @org.jetbrains.annotations.NotNull
    public final java.util.List<java.lang.String> getKeyParts() {
        return this.keyParts;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getExpiresAt() {
        return this.expiresAt;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.DecryptKeys getDecryptKeys() {
        return this.decryptKeys;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getIv2() {
        return this.iv2;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getPayload2() {
        return this.payload2;
    }
}
