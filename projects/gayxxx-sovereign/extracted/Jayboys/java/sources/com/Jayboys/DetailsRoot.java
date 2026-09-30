package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\t\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u001a\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001BO\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u0012\u0006\u0010\u0006\u001a\u00020\u0005\u0012\b\b\u0001\u0010\u0007\u001a\u00020\u0005\u0012\u0006\u0010\b\u001a\u00020\u0005\u0012\b\b\u0001\u0010\t\u001a\u00020\u0005\u0012\b\b\u0001\u0010\n\u001a\u00020\u000b\u0012\b\b\u0001\u0010\f\u001a\u00020\u0005¢\u0006\u0004\b\r\u0010\u000eJ\t\u0010\u001a\u001a\u00020\u0003HÆ\u0003J\t\u0010\u001b\u001a\u00020\u0005HÆ\u0003J\t\u0010\u001c\u001a\u00020\u0005HÆ\u0003J\t\u0010\u001d\u001a\u00020\u0005HÆ\u0003J\t\u0010\u001e\u001a\u00020\u0005HÆ\u0003J\t\u0010\u001f\u001a\u00020\u0005HÆ\u0003J\t\u0010 \u001a\u00020\u000bHÆ\u0003J\t\u0010!\u001a\u00020\u0005HÆ\u0003JY\u0010\"\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u00032\b\b\u0002\u0010\u0004\u001a\u00020\u00052\b\b\u0002\u0010\u0006\u001a\u00020\u00052\b\b\u0003\u0010\u0007\u001a\u00020\u00052\b\b\u0002\u0010\b\u001a\u00020\u00052\b\b\u0003\u0010\t\u001a\u00020\u00052\b\b\u0003\u0010\n\u001a\u00020\u000b2\b\b\u0003\u0010\f\u001a\u00020\u0005HÆ\u0001J\u0014\u0010#\u001a\u00020\u000b2\b\u0010$\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010%\u001a\u00020&HÖ\u0081\u0004J\n\u0010'\u001a\u00020\u0005HÖ\u0081\u0004R\u0011\u0010\u0002\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u0011\u0010\u0004\u001a\u00020\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u0011\u0010\u0012R\u0011\u0010\u0006\u001a\u00020\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u0013\u0010\u0012R\u0016\u0010\u0007\u001a\u00020\u00058\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0014\u0010\u0012R\u0011\u0010\b\u001a\u00020\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0012R\u0016\u0010\t\u001a\u00020\u00058\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0016\u0010\u0012R\u0016\u0010\n\u001a\u00020\u000b8\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0018R\u0016\u0010\f\u001a\u00020\u00058\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0012¨\u0006("}, d2 = {"Lcom/Jayboys/DetailsRoot;", "", "id", "", "code", "", "title", "posterUrl", "description", "createdAt", "ownerPrivate", "", "embedFrameUrl", "<init>", "(JLjava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZLjava/lang/String;)V", "getId", "()J", "getCode", "()Ljava/lang/String;", "getTitle", "getPosterUrl", "getDescription", "getCreatedAt", "getOwnerPrivate", "()Z", "getEmbedFrameUrl", "component1", "component2", "component3", "component4", "component5", "component6", "component7", "component8", "copy", "equals", "other", "hashCode", "", "toString", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class DetailsRoot {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String code;

    @com.fasterxml.jackson.annotation.JsonProperty("created_at")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String createdAt;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String description;

    @com.fasterxml.jackson.annotation.JsonProperty("embed_frame_url")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String embedFrameUrl;
    private final long id;

    @com.fasterxml.jackson.annotation.JsonProperty("owner_private")
    private final boolean ownerPrivate;

    @com.fasterxml.jackson.annotation.JsonProperty("poster_url")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String posterUrl;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String title;

    public static /* synthetic */ com.Jayboys.DetailsRoot copy$default(com.Jayboys.DetailsRoot detailsRoot, long j, java.lang.String str, java.lang.String str2, java.lang.String str3, java.lang.String str4, java.lang.String str5, boolean z, java.lang.String str6, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            j = detailsRoot.id;
        }
        long j2 = j;
        if ((i & 2) != 0) {
            str = detailsRoot.code;
        }
        java.lang.String str7 = str;
        if ((i & 4) != 0) {
            str2 = detailsRoot.title;
        }
        java.lang.String str8 = str2;
        if ((i & 8) != 0) {
            str3 = detailsRoot.posterUrl;
        }
        return detailsRoot.copy(j2, str7, str8, str3, (i & 16) != 0 ? detailsRoot.description : str4, (i & 32) != 0 ? detailsRoot.createdAt : str5, (i & 64) != 0 ? detailsRoot.ownerPrivate : z, (i & 128) != 0 ? detailsRoot.embedFrameUrl : str6);
    }

    /* JADX INFO: renamed from: component1, reason: from getter */
    public final long getId() {
        return this.id;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getCode() {
        return this.code;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getTitle() {
        return this.title;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component4, reason: from getter */
    public final java.lang.String getPosterUrl() {
        return this.posterUrl;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component5, reason: from getter */
    public final java.lang.String getDescription() {
        return this.description;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component6, reason: from getter */
    public final java.lang.String getCreatedAt() {
        return this.createdAt;
    }

    /* JADX INFO: renamed from: component7, reason: from getter */
    public final boolean getOwnerPrivate() {
        return this.ownerPrivate;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component8, reason: from getter */
    public final java.lang.String getEmbedFrameUrl() {
        return this.embedFrameUrl;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.DetailsRoot copy(long id, @org.jetbrains.annotations.NotNull java.lang.String code, @org.jetbrains.annotations.NotNull java.lang.String title, @com.fasterxml.jackson.annotation.JsonProperty("poster_url") @org.jetbrains.annotations.NotNull java.lang.String posterUrl, @org.jetbrains.annotations.NotNull java.lang.String description, @com.fasterxml.jackson.annotation.JsonProperty("created_at") @org.jetbrains.annotations.NotNull java.lang.String createdAt, @com.fasterxml.jackson.annotation.JsonProperty("owner_private") boolean ownerPrivate, @com.fasterxml.jackson.annotation.JsonProperty("embed_frame_url") @org.jetbrains.annotations.NotNull java.lang.String embedFrameUrl) {
        return new com.Jayboys.DetailsRoot(id, code, title, posterUrl, description, createdAt, ownerPrivate, embedFrameUrl);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Jayboys.DetailsRoot)) {
            return false;
        }
        com.Jayboys.DetailsRoot detailsRoot = (com.Jayboys.DetailsRoot) other;
        return this.id == detailsRoot.id && kotlin.jvm.internal.Intrinsics.areEqual(this.code, detailsRoot.code) && kotlin.jvm.internal.Intrinsics.areEqual(this.title, detailsRoot.title) && kotlin.jvm.internal.Intrinsics.areEqual(this.posterUrl, detailsRoot.posterUrl) && kotlin.jvm.internal.Intrinsics.areEqual(this.description, detailsRoot.description) && kotlin.jvm.internal.Intrinsics.areEqual(this.createdAt, detailsRoot.createdAt) && this.ownerPrivate == detailsRoot.ownerPrivate && kotlin.jvm.internal.Intrinsics.areEqual(this.embedFrameUrl, detailsRoot.embedFrameUrl);
    }

    public int hashCode() {
        return (((((((((((((com.Jayboys.DetailsRoot$$ExternalSyntheticBackport0.m(this.id) * 31) + this.code.hashCode()) * 31) + this.title.hashCode()) * 31) + this.posterUrl.hashCode()) * 31) + this.description.hashCode()) * 31) + this.createdAt.hashCode()) * 31) + com.Jayboys.DetailsRoot$$ExternalSyntheticBackport1.m(this.ownerPrivate)) * 31) + this.embedFrameUrl.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "DetailsRoot(id=" + this.id + ", code=" + this.code + ", title=" + this.title + ", posterUrl=" + this.posterUrl + ", description=" + this.description + ", createdAt=" + this.createdAt + ", ownerPrivate=" + this.ownerPrivate + ", embedFrameUrl=" + this.embedFrameUrl + ')';
    }

    public DetailsRoot(long id, @org.jetbrains.annotations.NotNull java.lang.String code, @org.jetbrains.annotations.NotNull java.lang.String title, @com.fasterxml.jackson.annotation.JsonProperty("poster_url") @org.jetbrains.annotations.NotNull java.lang.String posterUrl, @org.jetbrains.annotations.NotNull java.lang.String description, @com.fasterxml.jackson.annotation.JsonProperty("created_at") @org.jetbrains.annotations.NotNull java.lang.String createdAt, @com.fasterxml.jackson.annotation.JsonProperty("owner_private") boolean ownerPrivate, @com.fasterxml.jackson.annotation.JsonProperty("embed_frame_url") @org.jetbrains.annotations.NotNull java.lang.String embedFrameUrl) {
        this.id = id;
        this.code = code;
        this.title = title;
        this.posterUrl = posterUrl;
        this.description = description;
        this.createdAt = createdAt;
        this.ownerPrivate = ownerPrivate;
        this.embedFrameUrl = embedFrameUrl;
    }

    public final long getId() {
        return this.id;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getCode() {
        return this.code;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getTitle() {
        return this.title;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getPosterUrl() {
        return this.posterUrl;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getDescription() {
        return this.description;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getCreatedAt() {
        return this.createdAt;
    }

    public final boolean getOwnerPrivate() {
        return this.ownerPrivate;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getEmbedFrameUrl() {
        return this.embedFrameUrl;
    }
}
