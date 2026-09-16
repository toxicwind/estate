package com.Gaycock4U;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000$\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u000e\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u001b\u0012\b\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\b\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\u0004\b\u0006\u0010\u0007J\u0010\u0010\r\u001a\u0004\u0018\u00010\u0003HÆ\u0003¢\u0006\u0002\u0010\tJ\u000b\u0010\u000e\u001a\u0004\u0018\u00010\u0005HÆ\u0003J&\u0010\u000f\u001a\u00020\u00002\n\b\u0002\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0002\u0010\u0004\u001a\u0004\u0018\u00010\u0005HÆ\u0001¢\u0006\u0002\u0010\u0010J\u0014\u0010\u0011\u001a\u00020\u00032\b\u0010\u0012\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0013\u001a\u00020\u0014HÖ\u0081\u0004J\n\u0010\u0015\u001a\u00020\u0016HÖ\u0081\u0004R\u0015\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\n\n\u0002\u0010\n\u001a\u0004\b\b\u0010\tR\u0013\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\f¨\u0006\u0017"}, d2 = {"Lcom/Gaycock4U/InfoResponse;", "", "success", "", "data", "Lcom/Gaycock4U/VideoData;", "<init>", "(Ljava/lang/Boolean;Lcom/Gaycock4U/VideoData;)V", "getSuccess", "()Ljava/lang/Boolean;", "Ljava/lang/Boolean;", "getData", "()Lcom/Gaycock4U/VideoData;", "component1", "component2", "copy", "(Ljava/lang/Boolean;Lcom/Gaycock4U/VideoData;)Lcom/Gaycock4U/InfoResponse;", "equals", "other", "hashCode", "", "toString", "", "Gaycock4U"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class InfoResponse {

    @org.jetbrains.annotations.Nullable
    private final com.Gaycock4U.VideoData data;

    @org.jetbrains.annotations.Nullable
    private final java.lang.Boolean success;

    public static /* synthetic */ com.Gaycock4U.InfoResponse copy$default(com.Gaycock4U.InfoResponse infoResponse, java.lang.Boolean bool, com.Gaycock4U.VideoData videoData, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            bool = infoResponse.success;
        }
        if ((i & 2) != 0) {
            videoData = infoResponse.data;
        }
        return infoResponse.copy(bool, videoData);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.Boolean getSuccess() {
        return this.success;
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final com.Gaycock4U.VideoData getData() {
        return this.data;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Gaycock4U.InfoResponse copy(@org.jetbrains.annotations.Nullable java.lang.Boolean success, @org.jetbrains.annotations.Nullable com.Gaycock4U.VideoData data) {
        return new com.Gaycock4U.InfoResponse(success, data);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Gaycock4U.InfoResponse)) {
            return false;
        }
        com.Gaycock4U.InfoResponse infoResponse = (com.Gaycock4U.InfoResponse) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.success, infoResponse.success) && kotlin.jvm.internal.Intrinsics.areEqual(this.data, infoResponse.data);
    }

    public int hashCode() {
        return ((this.success == null ? 0 : this.success.hashCode()) * 31) + (this.data != null ? this.data.hashCode() : 0);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "InfoResponse(success=" + this.success + ", data=" + this.data + ')';
    }

    public InfoResponse(@org.jetbrains.annotations.Nullable java.lang.Boolean success, @org.jetbrains.annotations.Nullable com.Gaycock4U.VideoData data) {
        this.success = success;
        this.data = data;
    }

    @org.jetbrains.annotations.Nullable
    public final com.Gaycock4U.VideoData getData() {
        return this.data;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.Boolean getSuccess() {
        return this.success;
    }
}
